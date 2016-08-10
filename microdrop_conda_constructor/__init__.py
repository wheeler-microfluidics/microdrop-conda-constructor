import pkg_resources as pkg
import subprocess as sp
import tempfile as tmp

import jinja2
import microdrop_conda_constructor as mc
import path_helpers as ph
import pip_helpers


def build_template(major_version, output_path, cmd_func):
    '''
    Args
    ----

        major_version (int) : Major Microdrop version number.
        output_path (str) : If an existing directory is specified, built file
            is moved to specified directory with filename from build.
            Otherwise, built file is renamed to specified output file path.
        cmd_func (function) : Call-back function that takes a recipe/output
            directory as a single argument and returns the path of the built
            file.

    Returns
    -------

        (path_helpers.path) : Returns the path of the built file.
    '''
    package_str = 'microdrop>={}.0,<{}.0'.format(major_version,
                                                 major_version + 1)
    conda_package_name = 'microdrop-{}.0'.format(major_version)
    output_path = ph.path(output_path)

    # Get directory containing static templates.
    static_root = ph.path(pkg.resource_filename('microdrop_conda_constructor',
                                                'static'))

    # Get directory for Conda Microdrop package recipe template.
    template_root = static_root.joinpath('conda.microdrop.template')

    # Create temporary output directory.
    output_root = tmp.mkdtemp(prefix=template_root.name + '-')

    try:
        # Generate recipe for specified Microdrop version.
        mc.generate_recipe(package_str=package_str,
                           conda_package_name=conda_package_name,
                           template_root=template_root,
                           output_root=output_root)
        # Move built package archive to output path.
        archive_path = cmd_func(output_root.dirs()[0])
        if output_path.isdir():
            # Output path is directory.  Move archive to directory.
            output_path = output_path.joinpath(archive_path.name)
        archive_path.copy(output_path)
        return output_path
    finally:
        output_root.rmtree()


def build_conda_microdrop(major_version, output_path):
    '''
    Generate Conda package archive for latest Microdrop version using recipe.
    '''
    def build_cmd(output_root):
        # Use `conda build` to build Microdrop Conda package.
        sp.check_call(['conda', 'build', output_root])
        output_path = sp.check_output(['conda', 'build', '--output',
                                       output_root], stderr=sp.PIPE).strip()
        # Return path to built Microdrop Conda package.
        return ph.path(output_path)
    return build_template(major_version, output_path, build_cmd)


def build_miniconda_microdrop(major_version, output_path):
    '''
    Generate Miniconda `exe` installer for latest version of Microdrop using
    `constructor`.
    '''
    def build_cmd(output_root):
        # Use `constructor` to build Microdrop Miniconda installer.
        sp.check_call(['constructor', output_root])
        # Return path to built Microdrop Miniconda installer.
        return output_root.files('*.exe')[0]
    return build_template(major_version, output_path, build_cmd)


def generate_recipe(package_str, conda_package_name, template_root,
                    output_root, overwrite=False):
    '''
    Generate recipe for latest Microdrop version on PyPi.
    '''
    package_name, releases = pip_helpers.get_releases(package_str, pre=True)
    versions = releases.keys()
    output_root = ph.path(output_root)
    template_root = ph.path(template_root)

    for version_i in versions[-1:]:
        output_root_i = output_root.joinpath('microdrop-{}'.format(version_i))
        output_root_i.makedirs_p()

        for template_file in template_root.files():
            output_path_i = output_root_i.joinpath(template_file.name)

            if output_path_i.isfile() and not overwrite:
                raise IOError('Output file exists {}.  Use `-f` to overwrite.'
                            .format(output_path_i))

            with template_file.open('r') as template_fhandle:
                try:
                    template = jinja2.Template(template_fhandle.read())
                except:
                    template_file.copy(output_path_i)
                else:
                    text_i = template.render(conda_package_name=
                                             conda_package_name,
                                             version=version_i)
                    with output_path_i.open('w') as output:
                        output.write(text_i)
