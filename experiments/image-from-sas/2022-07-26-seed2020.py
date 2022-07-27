#! /usr/bin/env python

import os
import sys
import json, glob, shutil

from lab.environments import LocalEnvironment
from lab.experiment import Experiment
from lab import tools
from lab.reports import Attribute, geometric_mean

from downward import suites
from downward.reports.absolute import AbsoluteReport


# Copied from common_setup.py of issue733
def get_script():
    """Get file name of main script."""
    return tools.get_script_path()


def get_script_dir():
    """Get directory of main script.

    Usually a relative directory (depends on how it was called by the user.)"""
    return os.path.dirname(get_script())

# def get_repo_base():
#     """Get base directory of the repository, as an absolute path.

#     Search upwards in the directory tree from the main script until a
#     directory with a subdirectory named ".hg" is found.

#     Abort if the repo base cannot be found."""
#     path = os.path.abspath(get_script_dir())
#     while os.path.dirname(path) != path:
#         if os.path.exists(os.path.join(path, ".hg")):
#             return path
#         path = os.path.dirname(path)
#     sys.exit("repo base could not be found")


def get_base_dir():
    """Assume that this script always lives in the base dir of the infrastructure."""
    return os.path.abspath(get_script_dir())

def get_path_level_up(path):
    return os.path.dirname(path)

def get_planner_dir():
    return get_path_level_up(get_path_level_up(get_base_dir()))


REPO_DIR = get_planner_dir()
# BENCHMARKS_DIR = os.environ["DOWNWARD_BENCHMARKS_IPC2018"]
ENV = LocalEnvironment(processes=48)

# optimal strips suite
SUITE = ['airport', 'barman-opt11-strips', 'barman-opt14-strips', 'blocks',
'childsnack-opt14-strips', 'depot', 'driverlog', 'elevators-opt08-strips',
'elevators-opt11-strips', 'floortile-opt11-strips', 'floortile-opt14-strips',
'freecell', 'ged-opt14-strips', 'grid', 'gripper', 'hiking-opt14-strips',
'logistics00', 'logistics98', 'miconic', 'movie', 'mprime', 'mystery',
'nomystery-opt11-strips', 'openstacks-opt08-strips', 'openstacks-opt11-strips',
'openstacks-opt14-strips', 'openstacks-strips', 'parcprinter-08-strips',
'parcprinter-opt11-strips', 'parking-opt11-strips', 'parking-opt14-strips',
'pathways-noneg', 'pegsol-08-strips', 'pegsol-opt11-strips',
'pipesworld-notankage', 'pipesworld-tankage', 'psr-small', 'rovers',
'satellite', 'scanalyzer-08-strips', 'scanalyzer-opt11-strips',
'sokoban-opt08-strips', 'sokoban-opt11-strips', 'storage',
'tetris-opt14-strips', 'tidybot-opt11-strips', 'tidybot-opt14-strips', 'tpp',
'transport-opt08-strips', 'transport-opt11-strips', 'transport-opt14-strips',
'trucks-strips', 'visitall-opt11-strips', 'visitall-opt14-strips',
'woodworking-opt08-strips', 'woodworking-opt11-strips', 'zenotravel',
'ss_barman', 'ss_ferry', 'ss_goldminer', 'ss_grid', 'ss_hanoi', 'ss_hiking',
'ss_npuzzle', 'ss_spanner']

# conditional effects suite
SUITE.extend(['briefcaseworld', 'cavediving-14-adl', 'citycar-opt14-adl',
'fsc-blocks', 'fsc-grid-a1', 'fsc-grid-a2', 'fsc-grid-r', 'fsc-hall',
'fsc-visualmarker', 'gedp-ds2ndp', 'miconic-simpleadl', 't0-adder', 't0-coins',
't0-comm', 't0-grid-dispose', 't0-grid-push', 't0-grid-trash', 't0-sortnet',
't0-sortnet-alt', 't0-uts', 'ss_briefcaseworld', 'ss_cavediving', 'ss_citycar',
'ss_maintenance', 'ss_maintenance_large', 'ss_schedule'])


# For the fdr generated tasks
BENCHMARKS_DIR =  '/data/software/FDR-benchmark'
SUITE = ["bidirectional-bi-partite-sas", "bi-partite-sas", "chain-0.1-sas", "chain-0.25-sas", "chain-0.5-sas", "chain-0.75-sas", "dag-0.1-sas", "dag-0.25-sas", "dag-0.5-sas", "dag-0.75-sas", "directed-chain-sas", "fork-sas", "inverted-fork-sas", "polytree-0.1-sas", "polytree-0.25-sas", "polytree-0.5-sas", "polytree-0.75-sas", "random-0.1-sas", "random-0.25-sas", "random-0.5-sas", "random-0.75-sas", "star-0.1-sas", "star-0.25-sas", "star-0.5-sas", "star-0.75-sas", "tree-sas"]

# For the fdr generated tasks from PDDL
BENCHMARKS_DIR =  '/data/software/FDR-benchmarks-from-PDDL/07-20-2022'
SUITE = ['ss_grid', 'briefcaseworld', 't0-uts', 'ss_npuzzle', 'ss_hanoi', 'ss_citycar', 't0-sortnet-alt', 't0-grid-push', 'ss_cavediving', 'gedp-ds2ndp', 't0-adder', 't0-grid-dispose', 'ss_hiking', 'ss_maintenance_large', 'ss_ferry', 'trucks-strips', 'fsc-grid-r', 'ss_barman', 'fsc-hall', 't0-coins', 'fsc-grid-a2', 't0-comm', 'pathways-noneg', 'ss_maintenance', 'ss_schedule', 'openstacks-strips', 't0-grid-trash', 'ss_spanner', 'ss_goldminer', 'ss_briefcaseworld', 'fsc-grid-a1', 't0-sortnet', 'fsc-visualmarker', 'fsc-blocks']
SUITE = [f'rg-{d}' for d in SUITE]


# Create a new experiment.
exp = Experiment(environment=ENV)

# Absolute path to executable
planner = os.path.join(os.path.abspath(REPO_DIR), 'delfi', 'create_image_grounded_sas.py')

for task in suites.build_suite(BENCHMARKS_DIR, SUITE):
    run = exp.add_run()
    # Create symbolic links and aliases. This is optional. We
    # could also use absolute paths in add_command().
    run.add_resource('problem', task.problem_file, symlink=True)
    # We could also use exp.add_resource() for the binary.
    run.add_command(
                'run-planner',
                [sys.executable,  planner, '{problem}'],
                time_limit=1800,
                memory_limit=7600)

    run.set_property('domain', task.domain)
    run.set_property('problem', task.problem)
    run.set_property('algorithm', "image-generation")
    # Every run has to have a unique id in the form of a list.
    # The algorithm name is only really needed when there are
    # multiple algorithms.
    run.set_property('id', ["image-generation", task.domain, task.problem])

# Add step that writes experiment files to disk.
exp.add_step('build', exp.build)

# Add step that executes all runs.
exp.add_step('start', exp.start_runs)



def get_static_data(folder):
    with open(os.path.join(folder, "static-properties"), "r") as f:
        return json.load(f)

def gather_generated_images():
    EXP_FOLDER = os.path.join("data", exp.name)
    DEST_FOLDER = os.path.join(EXP_FOLDER,"images")
    for folder in glob.glob(os.path.join(EXP_FOLDER, "runs-*","*")):
        data = get_static_data(folder)
        domain = data["domain"]
        problem = "-"+data["problem"].replace(".sas", ".pddl")+"-bolded-cs.png"
        print(problem)
        dest_domain = os.path.join(DEST_FOLDER, domain)
        os.makedirs(dest_domain, exist_ok=True)
        for f in glob.glob(os.path.join(folder, "output-*.png")):
            bname = os.path.basename(f)
            destname = os.path.join(dest_domain, problem)
            print("Copying %s into %s" % (bname, destname))

            shutil.copy2(f, destname)

exp.add_step("gather-generated-images", gather_generated_images)


# Parse the commandline and run the specified steps.
exp.run_steps()

