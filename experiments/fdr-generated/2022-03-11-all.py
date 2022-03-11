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


ALGORITHM_TO_COMMAND_LINE_STRING = {
    'h2-simpless-dks-blind': ['--symmetries', 'sym=structural_symmetries(search_symmetries=dks)', '--search', 'astar(blind,symmetries=sym,pruning=stubborn_sets_simple(min_required_pruning_ratio=0.01,expansions_before_checking_pruning_ratio=1000))'],
    'h2-simpless-dks-celmcut': ['--symmetries', 'sym=structural_symmetries(search_symmetries=dks)', '--search', 'astar(celmcut,symmetries=sym,pruning=stubborn_sets_simple(min_required_pruning_ratio=0.01,expansions_before_checking_pruning_ratio=1000))'],
    'h2-simpless-dks-900masb50ksccdfp': ['--symmetries', 'sym=structural_symmetries(search_symmetries=dks)', '--search', 'astar(merge_and_shrink(shrink_strategy=shrink_bisimulation(greedy=false),merge_strategy=merge_sccs(order_of_sccs=topological,merge_selector=score_based_filtering(scoring_functions=[goal_relevance,dfp,total_order(atomic_before_product=false,atomic_ts_order=reverse_level,product_ts_order=new_to_old)])),label_reduction=exact(before_shrinking=true,before_merging=false),max_states=50000,threshold_before_merge=1,main_loop_max_time=900),symmetries=sym,pruning=stubborn_sets_simple(min_required_pruning_ratio=0.01,expansions_before_checking_pruning_ratio=1000))'],
    'h2-simpless-dks-900masb50ksbmiasm': ['--symmetries', 'sym=structural_symmetries(search_symmetries=dks)', '--search', 'astar(merge_and_shrink(shrink_strategy=shrink_bisimulation(greedy=false),merge_strategy=merge_stateless(merge_selector=score_based_filtering(scoring_functions=[sf_miasm(shrink_strategy=shrink_bisimulation,max_states=50000),total_order(atomic_before_product=true,atomic_ts_order=reverse_level,product_ts_order=old_to_new)])),label_reduction=exact(before_shrinking=true,before_merging=false),max_states=50000,threshold_before_merge=1,main_loop_max_time=900),symmetries=sym,pruning=stubborn_sets_simple(min_required_pruning_ratio=0.01,expansions_before_checking_pruning_ratio=1000))'],
    # # we do not use h2 with miasm on purpose, because it suffers a lot from missing "left-over mutexes"
    # 'simpless-dks-masb50kmiasmdfp': ['--symmetries', 'sym=structural_symmetries(search_symmetries=dks)', '--search', 'astar(merge_and_shrink(shrink_strategy=shrink_bisimulation(greedy=false),merge_strategy=merge_precomputed(merge_tree=miasm(abstraction=miasm_merge_and_shrink(),fallback_merge_selector=score_based_filtering(scoring_functions=[goal_relevance,dfp,total_order(atomic_ts_order=reverse_level,product_ts_order=new_to_old,atomic_before_product=false)]))),label_reduction=exact(before_shrinking=true,before_merging=false),max_states=50000,threshold_before_merge=1,main_loop_max_time=900),symmetries=sym,pruning=stubborn_sets_simple(min_required_pruning_ratio=0.01,expansions_before_checking_pruning_ratio=1000))'],
    'h2-simpless-dks-900masginfsccdfp': ['--symmetries', 'sym=structural_symmetries(search_symmetries=dks)', '--search', 'astar(merge_and_shrink(shrink_strategy=shrink_bisimulation(greedy=true),merge_strategy=merge_sccs(order_of_sccs=topological,merge_selector=score_based_filtering(scoring_functions=[goal_relevance,dfp,total_order(atomic_before_product=false,atomic_ts_order=level,product_ts_order=random)])),label_reduction=exact(before_shrinking=true,before_merging=false),max_states=infinity,threshold_before_merge=1,main_loop_max_time=900),symmetries=sym,pruning=stubborn_sets_simple(min_required_pruning_ratio=0.01,expansions_before_checking_pruning_ratio=1000))'],
    'h2-simpless-dks-cpdbshc900': ['--symmetries', 'sym=structural_symmetries(search_symmetries=dks)', '--search', 'astar(cpdbs(patterns=hillclimbing(max_time=900),symmetries=sym,pruning=stubborn_sets_simple(min_required_pruning_ratio=0.01,expansions_before_checking_pruning_ratio=1000))'],
    'h2-simpless-dks-zopdbsgenetic': ['--symmetries', 'sym=structural_symmetries(search_symmetries=dks)', '--search', 'astar(zopdbs(patterns=genetic(pdb_max_size=50000,num_collections=5,num_episodes=30,mutation_probability=0.01),symmetries=sym,pruning=stubborn_sets_simple(min_required_pruning_ratio=0.01,expansions_before_checking_pruning_ratio=1000))'],
    'h2-simpless-oss-blind': ['--symmetries', 'sym=structural_symmetries(search_symmetries=oss)', '--search', 'astar(blind,symmetries=sym,pruning=stubborn_sets_simple(min_required_pruning_ratio=0.01,expansions_before_checking_pruning_ratio=1000))'],
    'h2-simpless-oss-celmcut': ['--symmetries', 'sym=structural_symmetries(search_symmetries=oss)', '--search', 'astar(celmcut,symmetries=sym,pruning=stubborn_sets_simple(min_required_pruning_ratio=0.01,expansions_before_checking_pruning_ratio=1000))'],
    'h2-simpless-oss-900masb50ksccdfp': ['--symmetries', 'sym=structural_symmetries(search_symmetries=oss)', '--search', 'astar(merge_and_shrink(shrink_strategy=shrink_bisimulation(greedy=false),merge_strategy=merge_sccs(order_of_sccs=topological,merge_selector=score_based_filtering(scoring_functions=[goal_relevance,dfp,total_order(atomic_before_product=false,atomic_ts_order=reverse_level,product_ts_order=new_to_old)])),label_reduction=exact(before_shrinking=true,before_merging=false),max_states=50000,threshold_before_merge=1,main_loop_max_time=900,prune_unreachable_states=false),symmetries=sym,pruning=stubborn_sets_simple(min_required_pruning_ratio=0.01,expansions_before_checking_pruning_ratio=1000))'],
    'h2-simpless-oss-900masb50ksbmiasm': ['--symmetries', 'sym=structural_symmetries(search_symmetries=oss)', '--search', 'astar(merge_and_shrink(shrink_strategy=shrink_bisimulation(greedy=false),merge_strategy=merge_stateless(merge_selector=score_based_filtering(scoring_functions=[sf_miasm(shrink_strategy=shrink_bisimulation,max_states=50000),total_order(atomic_before_product=true,atomic_ts_order=reverse_level,product_ts_order=old_to_new)])),label_reduction=exact(before_shrinking=true,before_merging=false),max_states=50000,threshold_before_merge=1,main_loop_max_time=900,prune_unreachable_states=false),symmetries=sym,pruning=stubborn_sets_simple(min_required_pruning_ratio=0.01,expansions_before_checking_pruning_ratio=1000))'],
    # # we do not use h2 with miasm on purpose, because it suffers a lot from missing "left-over mutexes"
    # 'simpless-oss-masb50kmiasmdfp': ['--symmetries', 'sym=structural_symmetries(search_symmetries=oss)', '--search', 'astar(merge_and_shrink(shrink_strategy=shrink_bisimulation(greedy=false),merge_strategy=merge_precomputed(merge_tree=miasm(abstraction=miasm_merge_and_shrink(),fallback_merge_selector=score_based_filtering(scoring_functions=[goal_relevance,dfp,total_order(atomic_ts_order=reverse_level,product_ts_order=new_to_old,atomic_before_product=false)]))),label_reduction=exact(before_shrinking=true,before_merging=false),max_states=50000,threshold_before_merge=1,main_loop_max_time=900,prune_unreachable_states=false),symmetries=sym,pruning=stubborn_sets_simple(min_required_pruning_ratio=0.01,expansions_before_checking_pruning_ratio=1000))'],
    'h2-simpless-oss-masginfsccdfp': ['--symmetries', 'sym=structural_symmetries(search_symmetries=oss)', '--search', 'astar(merge_and_shrink(shrink_strategy=shrink_bisimulation(greedy=true),merge_strategy=merge_sccs(order_of_sccs=topological,merge_selector=score_based_filtering(scoring_functions=[goal_relevance,dfp,total_order(atomic_before_product=false,atomic_ts_order=level,product_ts_order=random)])),label_reduction=exact(before_shrinking=true,before_merging=false),max_states=infinity,threshold_before_merge=1,main_loop_max_time=900,prune_unreachable_states=false),symmetries=sym,pruning=stubborn_sets_simple(min_required_pruning_ratio=0.01,expansions_before_checking_pruning_ratio=1000))'],
    'h2-simpless-oss-cpdbshc900': ['--symmetries', 'sym=structural_symmetries(search_symmetries=oss)', '--search', 'astar(cpdbs(patterns=hillclimbing(max_time=900),symmetries=sym,pruning=stubborn_sets_simple(min_required_pruning_ratio=0.01,expansions_before_checking_pruning_ratio=1000))'],
    'h2-simpless-oss-zopdbsgenetic': ['--symmetries', 'sym=structural_symmetries(search_symmetries=oss)', '--search', 'astar(zopdbs(patterns=genetic(pdb_max_size=50000,num_collections=5,num_episodes=30,mutation_probability=0.01),symmetries=sym,pruning=stubborn_sets_simple(min_required_pruning_ratio=0.01,expansions_before_checking_pruning_ratio=1000))']
}


CONFIGS = []

for name, config in ALGORITHM_TO_COMMAND_LINE_STRING.items():
    driver_options=[]
    if "h2-" in name:
        driver_options=["--transform-task", "preprocess"]
    CONFIGS.append(IssueConfig(name, config, driver_options=driver_options))
        
ENVIRONMENT = LocalEnvironment(processes=48)

SUITE = ["bidirectional-bi-partite-sas", "bi-partite-sas", "chain-0.1-sas", "chain-0.25-sas", "chain-0.5-sas", "chain-0.75-sas", "dag-0.1-sas", "dag-0.25-sas", "dag-0.5-sas", "dag-0.75-sas", "directed-chain-sas", "fork-sas", "inverted-fork-sas", "polytree-0.1-sas", "polytree-0.25-sas", "polytree-0.5-sas", "polytree-0.75-sas", "random-0.1-sas", "random-0.25-sas", "random-0.5-sas", "random-0.75-sas", "star-0.1-sas", "star-0.25-sas", "star-0.5-sas", "star-0.75-sas", "tree-sas"]

SUITE = ["bidirectional-bi-partite-sas:p04-3758060068-4520-113-1-5-5-25.sas"]

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
