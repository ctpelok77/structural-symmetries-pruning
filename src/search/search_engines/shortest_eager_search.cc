#include "shortest_eager_search.h"

#include "../evaluation_context.h"
#include "../evaluator.h"
#include "../open_list_factory.h"
#include "../option_parser.h"
#include "../pruning_method.h"

#include "../algorithms/ordered_set.h"
#include "../task_utils/successor_generator.h"
#include "../tasks/root_task.h"

#include "../utils/logging.h"
#include "../structural_symmetries/group.h"

#include <cassert>
#include <cstdlib>
#include <memory>
#include <optional.hh>
#include <set>

using namespace std;

namespace eager_search {
ShortestEagerSearch::ShortestEagerSearch(const Options &opts)
    : SearchEngine(opts),
      reopen_closed_nodes(opts.get<bool>("reopen_closed")),
      open_list(opts.get<shared_ptr<OpenListFactory>>("open")->
                create_state_open_list()),
      f_evaluator(opts.get<shared_ptr<Evaluator>>("f_eval", nullptr)),
      preferred_operator_evaluators(opts.get_list<shared_ptr<Evaluator>>("preferred")),
      lazy_evaluator(opts.get<shared_ptr<Evaluator>>("lazy_evaluator", nullptr)),
      pruning_method(opts.get<shared_ptr<PruningMethod>>("pruning")) {
    if (lazy_evaluator && !lazy_evaluator->does_cache_estimates()) {
        cerr << "lazy_evaluator must cache its estimates" << endl;
        utils::exit_with(utils::ExitCode::SEARCH_INPUT_ERROR);
    }
    if (opts.contains("symmetries")) {
        group = opts.get<shared_ptr<Group>>("symmetries");
        if (group && !group->is_initialized()) {
            utils::g_log << "Initializing symmetries (eager search)" << endl;
            group->compute_symmetries(TaskProxy(*tasks::g_root_task));
        }

        if (use_dks()) {
            utils::g_log << "Setting group in registry for DKS search" << endl;
            state_registry.set_group(group);
        }
    } else {
        group = nullptr;
    }
}

bool ShortestEagerSearch::use_oss() const {
    return group && group->has_symmetries() && group->get_search_symmetries() == SearchSymmetries::OSS;
}

bool ShortestEagerSearch::use_dks() const {
    return group && group->has_symmetries() && group->get_search_symmetries() == SearchSymmetries::DKS;
}

void ShortestEagerSearch::initialize() {
    utils::g_log << "Conducting best first search"
                 << (reopen_closed_nodes ? " with" : " without")
                 << " reopening closed nodes, (real) bound = " << bound
                 << endl;
    assert(open_list);

    set<Evaluator *> evals;
    open_list->get_path_dependent_evaluators(evals);

    /*
      Collect path-dependent evaluators that are used for preferred operators
      (in case they are not also used in the open list).
    */
    for (const shared_ptr<Evaluator> &evaluator : preferred_operator_evaluators) {
        evaluator->get_path_dependent_evaluators(evals);
    }

    /*
      Collect path-dependent evaluators that are used in the f_evaluator.
      They are usually also used in the open list and will hence already be
      included, but we want to be sure.
    */
    if (f_evaluator) {
        f_evaluator->get_path_dependent_evaluators(evals);
    }

    /*
      Collect path-dependent evaluators that are used in the lazy_evaluator
      (in case they are not already included).
    */
    if (lazy_evaluator) {
        lazy_evaluator->get_path_dependent_evaluators(evals);
    }

    path_dependent_evaluators.assign(evals.begin(), evals.end());

    State initial_state = state_registry.get_initial_state();
    if (use_oss()) {
        vector<int> canonical_state = group->get_canonical_representative(initial_state);
        initial_state = state_registry.register_state_buffer(canonical_state);
    }
    for (Evaluator *evaluator : path_dependent_evaluators) {
        evaluator->notify_initial_state(initial_state);
    }

    /*
      Note: we consider the initial state as reached by a preferred
      operator.
    */
    EvaluationContext eval_context(initial_state, 0, true, &statistics, false, 0);

    statistics.inc_evaluated_states();

    if (open_list->is_dead_end(eval_context)) {
        utils::g_log << "Initial state is a dead end." << endl;
    } else {
        if (search_progress.check_progress(eval_context))
            statistics.print_checkpoint_line(0);
        start_f_value_statistics(eval_context);
        SearchNode node = search_space.get_node(initial_state);
        node.open_initial();

        open_list->insert(eval_context, initial_state.get_id());
    }

    print_initial_evaluator_values(eval_context);

    pruning_method->initialize(task);
}

void ShortestEagerSearch::print_statistics() const {
    statistics.print_detailed_statistics();
    search_space.print_statistics();
    pruning_method->print_statistics();
}

SearchStatus ShortestEagerSearch::step() {
    tl::optional<SearchNode> node;
    while (true) {
        if (open_list->empty()) {
            utils::g_log << "Completely explored state space -- no solution!" << endl;
            return FAILED;
        }
        StateID id = open_list->remove_min();
        State s = state_registry.lookup_state(id);
        node.emplace(search_space.get_node(s));

        if (node->is_closed())
            continue;

        /*
          We can pass calculate_preferred=false here since preferred
          operators are computed when the state is expanded.
        */
        EvaluationContext eval_context(s, node->get_g(), false, &statistics, false, node->get_d());

        if (lazy_evaluator) {
            /*
              With lazy evaluators (and only with these) we can have dead nodes
              in the open list.

              For example, consider a state s that is reached twice before it is expanded.
              The first time we insert it into the open list, we compute a finite
              heuristic value. The second time we insert it, the cached value is reused.

              During first expansion, the heuristic value is recomputed and might become
              infinite, for example because the reevaluation uses a stronger heuristic or
              because the heuristic is path-dependent and we have accumulated more
              information in the meantime. Then upon second expansion we have a dead-end
              node which we must ignore.
            */
            if (node->is_dead_end())
                continue;

            if (lazy_evaluator->is_estimate_cached(s)) {
                int old_h = lazy_evaluator->get_cached_estimate(s);
                int new_h = eval_context.get_evaluator_value_or_infinity(lazy_evaluator.get());
                if (open_list->is_dead_end(eval_context)) {
                    node->mark_as_dead_end();
                    statistics.inc_dead_ends();
                    continue;
                }
                if (new_h != old_h) {
                    open_list->insert(eval_context, id);
                    continue;
                }
            }
        }

        node->close();
        assert(!node->is_dead_end());
        update_f_value_statistics(eval_context);
        statistics.inc_expanded();
        break;
    }

    const State &s = node->get_state();
    if (check_goal_and_set_plan(s, group))
        return SOLVED;

    vector<OperatorID> applicable_ops;
    successor_generator.generate_applicable_ops(s, applicable_ops);

    /*
      TODO: When preferred operators are in use, a preferred operator will be
      considered by the preferred operator queues even when it is pruned.
    */
    pruning_method->prune_operators(s, applicable_ops);

    // This evaluates the expanded state (again) to get preferred ops
    EvaluationContext eval_context(s, node->get_g(), false, &statistics, true, node->get_d());
    ordered_set::OrderedSet<OperatorID> preferred_operators;
    for (const shared_ptr<Evaluator> &preferred_operator_evaluator : preferred_operator_evaluators) {
        collect_preferred_operators(eval_context,
                                    preferred_operator_evaluator.get(),
                                    preferred_operators);
    }

    for (OperatorID op_id : applicable_ops) {
        OperatorProxy op = task_proxy.get_operators()[op_id];
        if ((node->get_real_g() + op.get_cost()) >= bound)
            continue;

        /*
          NOTE: In orbit search tmp_registry has to survive as long as
                succ_state is used. This could be forever, but for heuristics
                that do not store per state information it is ok to keep it
                only for this operator application. In regular search it is not
                actually needed, but I don't see a way around having it there,
                too.
        */
        StateRegistry tmp_registry(task_proxy);
        StateRegistry *successor_registry = use_oss() ? &tmp_registry : &state_registry;
        State succ_state = successor_registry->get_successor_state(s, op);
        if (use_oss()) {
            vector<int> canonical_state = group->get_canonical_representative(succ_state);
            succ_state = state_registry.register_state_buffer(canonical_state);
        }
        statistics.inc_generated();
        bool is_preferred = preferred_operators.contains(op_id);

        SearchNode succ_node = search_space.get_node(succ_state);

        for (Evaluator *evaluator : path_dependent_evaluators) {
            evaluator->notify_state_transition(s, op_id, succ_state);
        }

        // Previously encountered dead end. Don't re-evaluate.
        if (succ_node.is_dead_end())
            continue;

        if (succ_node.is_new()) {
            // We have not seen this state before.
            // Evaluate and create a new node.

            // Careful: succ_node.get_g() is not available here yet,
            // hence the stupid computation of succ_g.
            // TODO: Make this less fragile.
            int succ_g = node->get_g() + get_adjusted_cost(op);

            /*
              NOTE: previous versions used the non-canocialized successor state
              here, but this lead to problems because the EvaluationContext was
              initialized with one state and the insertion was performed with
              another state.
             */
            EvaluationContext succ_eval_context(
                succ_state, succ_g, is_preferred, &statistics, false, node->get_d() + 1);
            statistics.inc_evaluated_states();

            if (open_list->is_dead_end(succ_eval_context)) {
                succ_node.mark_as_dead_end();
                statistics.inc_dead_ends();
                continue;
            }
            succ_node.open(*node, op, get_adjusted_cost(op));

            open_list->insert(succ_eval_context, succ_state.get_id());
            if (search_progress.check_progress(succ_eval_context)) {
                statistics.print_checkpoint_line(succ_node.get_g());
                reward_progress();
            }
        } else if (succ_node.get_g() > node->get_g() + get_adjusted_cost(op)
                   || (succ_node.get_g() == node->get_g() + get_adjusted_cost(op)
                       && succ_node.get_d() > node->get_d() + 1)) {
            // We found a new cheapest path to an open or closed state.
            if (reopen_closed_nodes) {
                if (succ_node.is_closed()) {
                    /*
                      TODO: It would be nice if we had a way to test
                      that reopening is expected behaviour, i.e., exit
                      with an error when this is something where
                      reopening should not occur (e.g. A* with a
                      consistent heuristic).
                    */
                    statistics.inc_reopened();
                }
                succ_node.reopen(*node, op, get_adjusted_cost(op));

                EvaluationContext succ_eval_context(
                    succ_state, succ_node.get_g(), is_preferred, &statistics, false, succ_node.get_d());

                /*
                  Note: our old code used to retrieve the h value from
                  the search node here. Our new code recomputes it as
                  necessary, thus avoiding the incredible ugliness of
                  the old "set_evaluator_value" approach, which also
                  did not generalize properly to settings with more
                  than one evaluator.

                  Reopening should not happen all that frequently, so
                  the performance impact of this is hopefully not that
                  large. In the medium term, we want the evaluators to
                  remember evaluator values for states themselves if
                  desired by the user, so that such recomputations
                  will just involve a look-up by the Evaluator object
                  rather than a recomputation of the evaluator value
                  from scratch.
                */
                open_list->insert(succ_eval_context, succ_state.get_id());
            } else {
                // If we do not reopen closed nodes, we just update the parent pointers.
                // Note that this could cause an incompatibility between
                // the g-value and the actual path that is traced back.
                succ_node.update_parent(*node, op, get_adjusted_cost(op));
            }
        }
    }

    return IN_PROGRESS;
}

void ShortestEagerSearch::reward_progress() {
    // Boost the "preferred operator" open lists somewhat whenever
    // one of the heuristics finds a state with a new best h value.
    open_list->boost_preferred();
}

void ShortestEagerSearch::dump_search_space() const {
    search_space.dump(task_proxy);
}

void ShortestEagerSearch::start_f_value_statistics(EvaluationContext &eval_context) {
    if (f_evaluator) {
        int f_value = eval_context.get_evaluator_value(f_evaluator.get());
        statistics.report_f_value_progress(f_value);
    }
}

/* TODO: HACK! This is very inefficient for simply looking up an h value.
   Also, if h values are not saved it would recompute h for each and every state. */
void ShortestEagerSearch::update_f_value_statistics(EvaluationContext &eval_context) {
    if (f_evaluator) {
        int f_value = eval_context.get_evaluator_value(f_evaluator.get());
        statistics.report_f_value_progress(f_value);
    }
}
}
