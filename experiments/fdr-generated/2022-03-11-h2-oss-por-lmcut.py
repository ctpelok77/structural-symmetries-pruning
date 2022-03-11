#! /usr/bin/env python3

import itertools
import os

from lab.environments import LocalEnvironment
from lab.reports import Attribute, arithmetic_mean, geometric_mean

from downward.reports.compare import ComparativeReport

from common_setup import IssueConfig, IssueExperiment

DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_NAME = os.path.splitext(os.path.basename(__file__))[0]
BENCHMARKS_DIR = '/data/software/FDR-benchmark'
REVISIONS = ['structural-symmetries-pruning']
CONFIGS = [
    # IssueConfig("blind-h2-oss-por", ["--symmetries", "sym=structural_symmetries(time_bound=0,search_symmetries=oss, stabilize_initial_state=false)","--search", "astar(blind(),symmetries=sym,pruning=stubborn_sets_simple(min_required_pruning_ratio=0.01,expansions_before_checking_pruning_ratio=1000))"],driver_options=["--transform-task", "preprocess"]),
    IssueConfig("lmcut-h2-oss-por", ["--symmetries", "sym=structural_symmetries(time_bound=0,search_symmetries=oss, stabilize_initial_state=false)","--search", "astar(lmcut(),symmetries=sym,pruning=stubborn_sets_simple(min_required_pruning_ratio=0.01,expansions_before_checking_pruning_ratio=1000))"],driver_options=["--transform-task", "preprocess"]),
    # IssueConfig("ms-us-h2-oss-por", ["--symmetries", "sym=structural_symmetries(time_bound=0,search_symmetries=oss, stabilize_initial_state=false)","--search", "astar(merge_and_shrink(transform=no_transform(), cache_estimates=true, merge_strategy=merge_strategy=merge_sccs(order_of_sccs=topological,merge_selector=score_based_filtering(scoring_functions=[goal_relevance,dfp,total_order])),shrink_strategy=shrink_strategy=shrink_bisimulation(greedy=false), prune_unreachable_states=false, prune_irrelevant_states=true, max_states=-1, max_states_before_merge=-1, threshold_before_merge=-1, verbosity=normal, main_loop_max_time=infinity),symmetries=sym,pruning=stubborn_sets_simple(min_required_pruning_ratio=0.01,expansions_before_checking_pruning_ratio=1000))"],driver_options=["--transform-task", "preprocess"]),
    # IssueConfig("cegar-h2-oss-por", ["--symmetries", "sym=structural_symmetries(time_bound=0,search_symmetries=oss, stabilize_initial_state=false)","--search", "astar(cegar(),symmetries=sym,pruning=stubborn_sets_simple(min_required_pruning_ratio=0.01,expansions_before_checking_pruning_ratio=1000))"],driver_options=["--transform-task", "preprocess"]),
    # IssueConfig("hmax-h2-oss-por", ["--symmetries", "sym=structural_symmetries(time_bound=0,search_symmetries=oss, stabilize_initial_state=false)","--search", "astar(hmax(),symmetries=sym,pruning=stubborn_sets_simple(min_required_pruning_ratio=0.01,expansions_before_checking_pruning_ratio=1000))"],driver_options=["--transform-task", "preprocess"]),
    # IssueConfig("ipdb-h2-oss-por", ["--symmetries", "sym=structural_symmetries(time_bound=0,search_symmetries=oss, stabilize_initial_state=false)","--search", "astar(ipdb(pdb_max_size=2000000, collection_max_size=20000000, num_samples=1000, min_improvement=10, max_time=infinity, random_seed=-1, max_time_dominance_pruning=infinity, transform=no_transform(), cache_estimates=true),symmetries=sym,pruning=stubborn_sets_simple(min_required_pruning_ratio=0.01,expansions_before_checking_pruning_ratio=1000))"],driver_options=["--transform-task", "preprocess"]),
]


ENVIRONMENT = LocalEnvironment(processes=48)

SUITE = ["bidirectional-bi-partite-sas", "bi-partite-sas", "chain-0.1-sas", "chain-0.25-sas", "chain-0.5-sas", "chain-0.75-sas", "dag-0.1-sas", "dag-0.25-sas", "dag-0.5-sas", "dag-0.75-sas", "directed-chain-sas", "fork-sas", "inverted-fork-sas", "polytree-0.1-sas", "polytree-0.25-sas", "polytree-0.5-sas", "polytree-0.75-sas", "random-0.1-sas", "random-0.25-sas", "random-0.5-sas", "random-0.75-sas", "star-0.1-sas", "star-0.25-sas", "star-0.5-sas", "star-0.75-sas", "tree-sas"]

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
    attributes=attributes,
)

# OLD_REVISION='a87197080a97'
# # fetch last data from experiments run in scripts repo
# exp.add_fetcher(
#     'data/2020-07-10-lmcut-oss-dks-eval',
#     filter_algorithm=[
#         '{}-lmcut-dks'.format(OLD_REVISION),
#         '{}-lmcut-oss'.format(OLD_REVISION),
#         '{}-lmcut-dks-stabinit'.format(OLD_REVISION),
#         '{}-lmcut-oss-stabinit'.format(OLD_REVISION),
#     ],
#     merge=True
# )

# exp.add_comparison_table_step(revisions=[OLD_REVISION, REVISION], attributes=attributes)

exp.run_steps()
