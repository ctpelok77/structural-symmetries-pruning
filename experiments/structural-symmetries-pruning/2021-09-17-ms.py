#! /usr/bin/env python3

from collections import defaultdict
import itertools
import os

from lab.environments import LocalEnvironment, BaselSlurmEnvironment
from lab.reports import Attribute, arithmetic_mean, geometric_mean

from downward.reports.compare import ComparativeReport
from downward.reports.scatter import ScatterPlotReport

import common_setup
from common_setup import IssueConfig, IssueExperiment

DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_NAME = os.path.splitext(os.path.basename(__file__))[0]
BENCHMARKS_DIR = os.environ['DOWNWARD_BENCHMARKS']
REVISIONS = ['536ecfbc9b14df7777ecc85bd1dd142bfc475f99']
CONFIGS = [
    IssueConfig('dks-ms-prunedead', ['--symmetries', 'sym=structural_symmetries(time_bound=0,search_symmetries=dks)', '--search', 'astar(merge_and_shrink(shrink_strategy=shrink_bisimulation(greedy=false),merge_strategy=merge_sccs(order_of_sccs=topological,merge_selector=score_based_filtering(scoring_functions=[goal_relevance,dfp,total_order(atomic_ts_order=reverse_level,product_ts_order=new_to_old,atomic_before_product=false,random_seed=2016)])),label_reduction=exact(before_shrinking=true,before_merging=false),max_states=50000,threshold_before_merge=1,prune_unreachable_states=true,prune_irrelevant_states=true),symmetries=sym,verbosity=silent)']),
    IssueConfig('dks-ms-pruneirrelevant', ['--symmetries', 'sym=structural_symmetries(time_bound=0,search_symmetries=dks)', '--search', 'astar(merge_and_shrink(shrink_strategy=shrink_bisimulation(greedy=false),merge_strategy=merge_sccs(order_of_sccs=topological,merge_selector=score_based_filtering(scoring_functions=[goal_relevance,dfp,total_order(atomic_ts_order=reverse_level,product_ts_order=new_to_old,atomic_before_product=false,random_seed=2016)])),label_reduction=exact(before_shrinking=true,before_merging=false),max_states=50000,threshold_before_merge=1,prune_unreachable_states=false,prune_irrelevant_states=true),symmetries=sym,verbosity=silent)']),
    IssueConfig('oss-ms-pruneirrelevant', ['--symmetries', 'sym=structural_symmetries(time_bound=0,search_symmetries=oss)', '--search', 'astar(merge_and_shrink(shrink_strategy=shrink_bisimulation(greedy=false),merge_strategy=merge_sccs(order_of_sccs=topological,merge_selector=score_based_filtering(scoring_functions=[goal_relevance,dfp,total_order(atomic_ts_order=reverse_level,product_ts_order=new_to_old,atomic_before_product=false,random_seed=2016)])),label_reduction=exact(before_shrinking=true,before_merging=false),max_states=50000,threshold_before_merge=1,prune_unreachable_states=false,prune_irrelevant_states=true),symmetries=sym,verbosity=silent)']),
]

SUITE = common_setup.DEFAULT_OPTIMAL_SUITE
ENVIRONMENT = BaselSlurmEnvironment(
    email="silvan.sievers@unibas.ch",
    partition="infai_2",
    export=[],
    # paths obtained via:
    # module purge
    # module -q load CMake/3.15.3-GCCcore-8.3.0
    # module -q load GCC/8.3.0
    # echo $PATH
    # echo $LD_LIBRARY_PATH
    setup='export PATH=/scicore/soft/apps/binutils/2.32-GCCcore-8.3.0/bin:/scicore/soft/apps/CMake/3.15.3-GCCcore-8.3.0/bin:/scicore/soft/apps/cURL/7.66.0-GCCcore-8.3.0/bin:/scicore/soft/apps/bzip2/1.0.8-GCCcore-8.3.0/bin:/scicore/soft/apps/ncurses/6.1-GCCcore-8.3.0/bin:/scicore/soft/apps/GCCcore/8.3.0/bin:/infai/sieverss/repos/bin:/infai/sieverss/local:/export/soft/lua_lmod/centos7/lmod/lmod/libexec:/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin:$PATH\nexport LD_LIBRARY_PATH=/scicore/soft/apps/binutils/2.32-GCCcore-8.3.0/lib:/scicore/soft/apps/cURL/7.66.0-GCCcore-8.3.0/lib:/scicore/soft/apps/bzip2/1.0.8-GCCcore-8.3.0/lib:/scicore/soft/apps/zlib/1.2.11-GCCcore-8.3.0/lib:/scicore/soft/apps/ncurses/6.1-GCCcore-8.3.0/lib:/scicore/soft/apps/GCCcore/8.3.0/lib64:/scicore/soft/apps/GCCcore/8.3.0/lib')

if common_setup.is_test_run():
    SUITE = IssueExperiment.DEFAULT_TEST_SUITE
    ENVIRONMENT = LocalEnvironment(processes=4)

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
        '{}-dks-ms-prunedead'.format(REVISION),
        '{}-dks-ms-pruneirrelevant'.format(REVISION),
        '{}-oss-ms-pruneirrelevant'.format(REVISION),
    ],
    attributes=attributes,
)

dks_ms_prunedead = '{}-dks-ms-prunedead'.format(REVISION)
dks_ms_pruneirrelevant = '{}-dks-ms-pruneirrelevant'.format(REVISION)
oss_ms_pruneirrelevant = '{}-oss-ms-pruneirrelevant'.format(REVISION)
algorithm_pairs = [
    (dks_ms_prunedead, dks_ms_pruneirrelevant),
    (dks_ms_prunedead, oss_ms_pruneirrelevant),
    (dks_ms_pruneirrelevant, oss_ms_pruneirrelevant),
]
exp.add_report(
    ComparativeReport(
        algorithm_pairs=algorithm_pairs,
        attributes=attributes,
    ),
    outfile=os.path.join(exp.eval_dir, exp.name+"-compare.html")
)

class FilterDomains:
    def __init__(self, algo1, algo2, attribute, factor):
        self.algo1 = algo1
        self.algo2 = algo2
        self.attribute = attribute
        self.factor = factor
        self.domain_problem_algo_attribute = defaultdict(dict)
        self.processed = False

    def collect_data(self, props):
        algo = props['algorithm']
        if algo != self.algo1 and algo != self.algo2:
            return False
        domain = props['domain']
        problem = props['problem']
        attribute = props.get(self.attribute, float('inf'))
        if problem not in self.domain_problem_algo_attribute[domain]:
            self.domain_problem_algo_attribute[domain][problem] = dict()
        self.domain_problem_algo_attribute[domain][problem][algo] = attribute
        return True

    def process_data(self, props):
        if not self.processed:
            self.processed = True
            self.interesting_domains = set()
            for domain, rest in self.domain_problem_algo_attribute.items():
                for problem, algo_expansions in rest.items():
                    assert len(algo_expansions) == 2, algo_expansions
                    assert self.algo1 in algo_expansions
                    assert self.algo2 in algo_expansions
                    if algo_expansions[self.algo1] > self.factor * algo_expansions[self.algo2] or algo_expansions[self.algo2] > self.factor * algo_expansions[self.algo1]:
                        # print(f"{domain} is interesting; {algo_expansions[self.algo1]}, {algo_expansions[self.algo2]}")
                        self.interesting_domains.add(domain)
        return True

    def filter_domains(self, props):
        return props['domain'] in self.interesting_domains

    def get_category(self, run1, run2):
        domain = run1['domain']
        assert domain == run2['domain']
        return domain

for algo1, algo2 in algorithm_pairs:
    filter_domains = FilterDomains(algo1, algo2, 'expansions_until_last_jump', 10)
    exp.add_report(
        ScatterPlotReport(
            filter=[filter_domains.collect_data, filter_domains.process_data, filter_domains.filter_domains],
            attributes=["expansions_until_last_jump"],
            relative=False,
            get_category=filter_domains.get_category,
            format='png',
        ),
        outfile=os.path.join(exp.eval_dir, algo1.replace('{}-'.format(REVISION), '') + "-" + algo2.replace('{}-'.format(REVISION), '') + "-expansions"),
    )

filter_domains = FilterDomains(dks_ms_pruneirrelevant, oss_ms_pruneirrelevant, 'memory', 2)
exp.add_report(
    ScatterPlotReport(
        filter=[filter_domains.collect_data, filter_domains.process_data, filter_domains.filter_domains],
        attributes=["memory"],
        relative=False,
        get_category=filter_domains.get_category,
        format='png',
    ),
    outfile=os.path.join(exp.eval_dir, dks_ms_pruneirrelevant.replace('{}-'.format(REVISION), '') + "-" + oss_ms_pruneirrelevant.replace('{}-'.format(REVISION), '') + "-memory"),
)

exp.run_steps()
