from __future__ import annotations

import os
import typing as t
from glob import glob

import pkg_resources
from tutor import hooks as tutor_hooks
from tutor.__about__ import __version_suffix__

from .__about__ import __version__

# Handle version suffix in nightly mode, just like tutor core
if __version_suffix__:
    __version__ += "-" + __version_suffix__

config = {
    "defaults": {
        "VERSION": __version__,
        # TODO: update DOCKER_IMAGE
        "DOCKER_IMAGE": "{{ DOCKER_REGISTRY }}krishnamadhavan/keesh-studio:{{ KEESHSTUDIO_VERSION }}",
        "MYSQL_DATABASE": "keeshstudio",
        "MYSQL_USERNAME": "keeshstudio",
        "REPOSITORY": "https://github.com/krishnamadhavan/keesh-studio.git",
        "REPOSITORY_VERSION": "{{ OPENEDX_COMMON_VERSION }}",
    },
    "unique": {
        "MYSQL_PASSWORD": "{{ 8|random_string }}",
        "SECRET_KEY": "{{ 24|random_string }}",
    }
}


# Configuration entries
# ----------------------------------------------------------------------------------------------------
tutor_hooks.Filters.CONFIG_DEFAULTS.add_items(
    [(f"KEESHSTUDIO_{key}", value) for key, value in config.get("defaults", {}).items()]
)

tutor_hooks.Filters.CONFIG_UNIQUE.add_items(
    [(f"KEESHSTUDIO_{key}", value) for key, value in config.get("unique", {}).items()]
)

tutor_hooks.Filters.CONFIG_OVERRIDES.add_items(
    list(config.get("overrides", {}).items())
)


# Initialization Tasks
# ----------------------------------------------------------------------------------------------------
MY_INIT_TASKS: list[tuple[str, tuple[str, ...]]] = [
    ("mysql", ("keeshstudio", "tasks", "mysql", "init")),
    ("lms", ("keeshstudio", "tasks", "lms", "init")),
    ("keeshstudio", ("keeshstudio", "tasks", "keeshstudio", "init")),
]

# For each task added to MY_INIT_TASKS, we load the task template
# and add it to the CLI_DO_INIT_TASKS filter, which tells Tutor to
# run it as part of the `init` job.
for service, template_path in MY_INIT_TASKS:
    full_path: str = pkg_resources.resource_filename(
        "tutorkeeshstudio", os.path.join("templates", *template_path)
    )
    with open(full_path, encoding="utf-8") as init_task_file:
        init_task: str = init_task_file.read()
    tutor_hooks.Filters.CLI_DO_INIT_TASKS.add_item((service, init_task))


# Docker Image Management
# ----------------------------------------------------------------------------------------------------
tutor_hooks.Filters.IMAGES_BUILD.add_items(
    [
        (
            "keeshstudio",
            ("plugins", "keeshstudio", "build", "keeshstudio"),
            "{{ KEESHSTUDIO_DOCKER_IMAGE }}",
            (),
        )
    ]
)

tutor_hooks.Filters.IMAGES_PULL.add_items(
    [
        (
            "keeshstudio",
            "{{ KEESHSTUDIO_DOCKER_IMAGE }}",
        )
    ]
)

tutor_hooks.Filters.IMAGES_PUSH.add_items(
    [
        (
            "keeshstudio",
            "{{ KEESHSTUDIO_DOCKER_IMAGE }}",
        )
    ]
)


# Mount keeshstudio
# ----------------------------------------------------------------------------------------------------
# Automount /openedx/discovery folder from the container
@tutor_hooks.Filters.COMPOSE_MOUNTS.add()
def _mount_keesh_studio(
    volumes: list[tuple[str, str]], name: str
) -> list[tuple[str, str]]:
    """
    When mounting keesh-studio with `--mount=/path/to/keesh-studio`,
    bind-mount the host repo in the keeshstudio container.
    """
    if name == "keesh-studio":
        _path = "/app/keesh-studio"
        volumes += [
            ("keeshstudio", _path),
            ("keeshstudio-job", _path),
        ]
    return volumes


# Public Host configuration
# ----------------------------------------------------------------------------------------------------
@tutor_hooks.Filters.APP_PUBLIC_HOSTS.add()
def _print_keeshstudio_public_hosts(
    hosts: list[str], context_name: t.Literal["local", "dev"]
) -> list[str]:
    if context_name == "dev":
        hosts += ["{{ KEESHSTUDIO_HOST }}:8120"]
    else:
        hosts += ["{{ KEESHSTUDIO_HOST }}"]
    return hosts


# Template Rendering
# ----------------------------------------------------------------------------------------------------
# Add the "templates" folder as a template root
tutor_hooks.Filters.ENV_TEMPLATE_ROOTS.add_items(
    [pkg_resources.resource_filename("tutorkeeshstudio", "templates")]
)

# Render the "build" and "apps" folders
tutor_hooks.Filters.ENV_TEMPLATE_TARGETS.add_items(
    [
        ("keeshstudio/build", "plugins"),
        ("keeshstudio/apps", "plugins"),
    ],
)

# For each file in tutorkeeshstudio/patches,
# apply a patch based on the file's name and contents.
for path in glob(
    os.path.join(
        pkg_resources.resource_filename("tutorkeeshstudio", "patches"),
        "*",
    )
):
    with open(path, encoding="utf-8") as patch_file:
        tutor_hooks.Filters.ENV_PATCHES.add_item((os.path.basename(path), patch_file.read()))
