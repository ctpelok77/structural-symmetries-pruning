#! /usr/bin/env python3

import itertools
import os

from lab.environments import LocalEnvironment
from lab.reports import Attribute, arithmetic_mean, geometric_mean

from downward.reports.compare import ComparativeReport

import common_setup
from common_setup import IssueConfig, IssueExperiment

DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_NAME = os.path.splitext(os.path.basename(__file__))[0]
BENCHMARKS_DIR = os.environ['DOWNWARD_BENCHMARKS']
REVISIONS = ['489d2364460e4e11a89925d6304f85bec9d2091a']
CONFIGS = [
    # IssueConfig("blind-oss-por", ["--symmetries", "sym=structural_symmetries(time_bound=0,search_symmetries=oss, stabilize_initial_state=false)","--search", "astar(blind(),symmetries=sym,pruning=stubborn_sets_simple(min_required_pruning_ratio=0.01,expansions_before_checking_pruning_ratio=1000))"]),
    IssueConfig("lmcut-oss-por", ["--symmetries", "sym=structural_symmetries(time_bound=0,search_symmetries=oss, stabilize_initial_state=false)","--search", "astar(lmcut(),symmetries=sym,pruning=stubborn_sets_simple(min_required_pruning_ratio=0.01,expansions_before_checking_pruning_ratio=1000))"]),
    IssueConfig("ms-us-oss-por", ["--symmetries", "sym=structural_symmetries(time_bound=0,search_symmetries=oss, stabilize_initial_state=false)","--search", "astar(merge_and_shrink(transform=no_transform(), cache_estimates=true, merge_strategy=merge_strategy=merge_sccs(order_of_sccs=topological,merge_selector=score_based_filtering(scoring_functions=[goal_relevance,dfp,total_order])),shrink_strategy=shrink_strategy=shrink_bisimulation(greedy=false), prune_unreachable_states=false, prune_irrelevant_states=true, max_states=-1, max_states_before_merge=-1, threshold_before_merge=-1, verbosity=normal, main_loop_max_time=infinity),symmetries=sym,pruning=stubborn_sets_simple(min_required_pruning_ratio=0.01,expansions_before_checking_pruning_ratio=1000))"]),
    IssueConfig("cegar-oss-por", ["--symmetries", "sym=structural_symmetries(time_bound=0,search_symmetries=oss, stabilize_initial_state=false)","--search", "astar(cegar(),symmetries=sym,pruning=stubborn_sets_simple(min_required_pruning_ratio=0.01,expansions_before_checking_pruning_ratio=1000))"]),
    IssueConfig("hmax-oss-por", ["--symmetries", "sym=structural_symmetries(time_bound=0,search_symmetries=oss, stabilize_initial_state=false)","--search", "astar(hmax(),symmetries=sym,pruning=stubborn_sets_simple(min_required_pruning_ratio=0.01,expansions_before_checking_pruning_ratio=1000))"]),
    IssueConfig("ipdb-oss-por", ["--symmetries", "sym=structural_symmetries(time_bound=0,search_symmetries=oss, stabilize_initial_state=false)","--search", "astar(ipdb(pdb_max_size=2000000, collection_max_size=20000000, num_samples=1000, min_improvement=10, max_time=infinity, random_seed=-1, max_time_dominance_pruning=infinity, transform=no_transform(), cache_estimates=true),symmetries=sym,pruning=stubborn_sets_simple(min_required_pruning_ratio=0.01,expansions_before_checking_pruning_ratio=1000))"]),
]

SUITE = common_setup.DEFAULT_OPTIMAL_SUITE
ENVIRONMENT = LocalEnvironment(processes=48)


exp = IssueExperiment(
    revisions=REVISIONS,
    configs=CONFIGS,
    environment=ENVIRONMENT,
)
exp.add_suite(BENCHMARKS_DIR, SUITE)

exp.add_parser(exp.EXITCODE_PARSER)
exp.add_parser(exp.TRANSLATOR_PARSER)
exp.add_parser(exp.SINGLE_SEARCH_PARSER)
exp.add_parser(exp.PLANNER_PARSER)

exp.add_parser('symmetries-parser.py')

exp.add_step('build', exp.build)
exp.add_step('start', exp.start_runs)
exp.add_fetcher(name='fetch')

extra_attributes=[
    Attribute('num_search_generators', absolute=True, min_wins=False),
    Attribute('num_operator_generators', absolute=True, min_wins=False),
    Attribute('num_total_generators', absolute=True, min_wins=False),
    Attribute('symmetry_graph_size', absolute=True, min_wins=True),
    Attribute('time_symmetries', absolute=False, min_wins=True, function=geometric_mean),
    Attribute('symmetry_group_order', absolute=True, min_wins=False),
]
attributes = list(exp.DEFAULT_TABLE_ATTRIBUTES)
attributes.extend(extra_attributes)

REVISION=REVISIONS[0]
exp.add_absolute_report_step(
    filter_algorithm=[
        '{}-lmcut-dks'.format(REVISION),
        '{}-lmcut-oss'.format(REVISION),
        '{}-lmcut-dks-stabinit'.format(REVISION),
        '{}-lmcut-oss-stabinit'.format(REVISION),
    ],
    attributes=attributes,
)

OLD_REVISION='a87197080a97'
# fetch last data from experiments run in scripts repo
exp.add_fetcher(
    'data/2020-07-10-lmcut-oss-dks-eval',
    filter_algorithm=[
        '{}-lmcut-dks'.format(OLD_REVISION),
        '{}-lmcut-oss'.format(OLD_REVISION),
        '{}-lmcut-dks-stabinit'.format(OLD_REVISION),
        '{}-lmcut-oss-stabinit'.format(OLD_REVISION),
    ],
    merge=True
)

exp.add_comparison_table_step(revisions=[OLD_REVISION, REVISION], attributes=attributes)

exp.run_steps()
