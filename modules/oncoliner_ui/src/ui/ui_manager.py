from typing import List, Union
import os
import sys
from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup
from htmlmin.minify import html_minify
import rjsmin
import rcssmin

# Add vcf-ops to the path
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', '..', '..', '..', 'shared', 'vcf_ops', 'src'))

from vcf_ops.constants import INTERSECTION_SYMBOL, UNION_SYMBOL  # noqa

from .utils import get_conf  # noqa
from .assessment_tab import AssessmentTab  # noqa
from .improvement_tab import ImprovementTab  # noqa
from .harmonization_tab import HarmonizationTab  # noqa

from .model.assessment.assessment_dao import AssessmentDAO  # noqa
from .model.improvement.improvement_dao import ImprovementDAO  # noqa
from .model.harmonization.harmonization_dao import HarmonizationDAO  # noqa


def generate_html(pipelines_evaluations_folders: List[str], output_file: str, pipelines_improvements_folders: Union[List[str], None], harmonization_folder: Union[str, None]):
    # Generate HTML files
    loader = FileSystemLoader(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'html_templates'))
    env = Environment(loader=loader)

    # Load operations
    def include_raw(name):
        source = loader.get_source(env, name)[0]
        # Minify JS
        if name.endswith('.js'):
            return Markup(rjsmin.jsmin(source))
        # Minify CSS
        elif name.endswith('.css'):
            return Markup(rcssmin.cssmin(source))
        return Markup(source)

    def include_cooked(template_path, **context):
        template = env.get_template(template_path)
        result = template.render(**context)
        # Minify JS
        if template_path.endswith('.js'):
            return rjsmin.jsmin(result)
        return result

    def include_encoded(name):
        # Escape " and # characters
        raw_src = loader.get_source(env, name)[0]
        return raw_src.replace('"', '\'').replace('#', '%23')

    pipelines_names = [os.path.basename(pipeline_folder) for pipeline_folder in pipelines_evaluations_folders]
    # Check pipeline_names are unique
    if len(pipelines_names) != len(set(pipelines_names)):
        raise ValueError(f'Pipeline names are not unique: {pipelines_names}. Please, rename their assessment folders')
    # If there are improvements, check they are the same pipelines
    if pipelines_improvements_folders:
        pipelines_improvements_names = [os.path.basename(pipeline_folder) for pipeline_folder in pipelines_improvements_folders]
        if set(pipelines_names) != set(pipelines_improvements_names):
            raise ValueError(
                f'Pipelines in evaluation and improvement folders are not the same: {pipelines_names} != {pipelines_improvements_names}')

    # Create assessment tab
    assessment_dao = AssessmentDAO(pipelines_evaluations_folders)
    assessment_tab = AssessmentTab(env, assessment_dao)

    # Create improvement tab
    improvement_dao = None
    improvement_tab = None
    if pipelines_improvements_folders:
        improvement_dao = ImprovementDAO(pipelines_improvements_folders)
        improvement_tab = ImprovementTab(env, improvement_dao)

    # Create harmonization tab
    harmonization_dao = None
    harmonization_tab = None
    if harmonization_folder:
        if not pipelines_improvements_folders:
            raise ValueError('Harmonization folder provided but no improvements folder provided')
        harmonization_dao = HarmonizationDAO(harmonization_folder, pipelines_improvements_folders)
        harmonization_tab = HarmonizationTab(env, harmonization_dao)

    def print_js_function(function, allParams, varParams=None):
        params = []
        for p in allParams:
            if varParams and p in varParams:
                params.append(f'{p}')
            else:
                params.append(f"'{p}'")
        paramStr = ', '.join(params)
        return f'{function}({paramStr})'

    def get_controller(tab):
        ctrl = None
        if tab == 'assessment':
            ctrl = assessment_tab
        elif tab == 'harmonization':
            ctrl = harmonization_tab
        elif tab == 'improvement':
            ctrl = improvement_tab
        else:
            raise ValueError(f'Invalid tab: {tab}')
        return ctrl

    def render_tab(tab):
        ctrl = get_controller(tab)
        if ctrl:
            return ctrl.render()
        else:
            return ''

    main_tabs = list(filter(lambda tab: get_controller(tab) is not None, ['assessment', 'harmonization', 'improvement']))

    env.globals['include_raw'] = include_raw
    env.globals['include_cooked'] = include_cooked
    env.globals['include_encoded'] = include_encoded
    env.globals['render_tab'] = render_tab
    env.globals['print_js_function'] = print_js_function
    env.globals['intersection_symbol'] = INTERSECTION_SYMBOL
    env.globals['union_symbol'] = UNION_SYMBOL

    # Global vars
    env.globals['conf'] = get_conf()

    template = env.get_template(os.path.join("index", "base.html"))

    with open(os.path.join(output_file), "w") as f:
        output_str = template.render(main_tabs=main_tabs)
        f.write(html_minify(output_str))
