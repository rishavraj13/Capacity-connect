"""Require explicit target bindings for every identifier-bearing app route."""

from django.urls import URLResolver, get_resolver, reverse

from apps.core.tests.route_audit import STATE_NAMES

TARGET_GROUPS = {
    "announcement": (
        "announcements:edit announcements:publish announcements:unpublish "
        "announcements:delete"
    ),
    "competency": "competency:edit competency:remove",
    "course": (
        "courses:detail courses:edit courses:publish courses:unpublish "
        "courses:module_add courses:enroll courses:participants "
        "assessments:course_list assessments:create feedback:course_submit "
        "feedback:course_summary"
    ),
    "module": "courses:module_edit courses:module_delete",
    "enrollment": "courses:drop courses:complete_module",
    "resource": (
        "library:detail library:edit library:delete library:publish "
        "library:unpublish library:download feedback:resource_submit "
        "feedback:resource_summary"
    ),
    "quiz": (
        "assessments:manage_detail assessments:edit assessments:delete "
        "assessments:question_add assessments:participation "
        "assessments:detail assessments:start"
    ),
    "question": "assessments:question_edit assessments:question_delete",
    "attempt": "assessments:take assessments:result",
    "award": "certificates:download",
    "feedback": "feedback:delete",
    "subject": (
        "catalog:subject_edit catalog:subject_deactivate catalog:subject_reactivate"
    ),
    "skill": "catalog:skill_edit catalog:skill_delete",
    "trainee_profile": "profiles:trainee_detail profiles:private_file",
    "trainer_profile": "profiles:trainer_detail",
    "qualification": "profiles:qualification_edit profiles:qualification_delete",
    "experience": "profiles:experience_edit profiles:experience_delete",
    "certificate": "profiles:certificate_edit profiles:certificate_delete",
    "trainee": "admin_approve_user admin_reject_user admin_change_role",
}
BINDINGS = {
    name: target for target, names in TARGET_GROUPS.items() for name in names.split()
}
SHARED_READS = frozenset(
    {"courses:detail", "library:detail", "library:download", "profiles:trainer_detail"}
)
SELF_ACTIONS = frozenset({"courses:enroll", "feedback:resource_submit"})
READ_ONLY = SHARED_READS | frozenset(
    {
        "profiles:trainee_detail",
        "profiles:private_file",
        "certificates:download",
        "assessments:manage_detail",
        "assessments:detail",
        "assessments:result",
        "assessments:participation",
        "assessments:course_list",
        "courses:participants",
        "feedback:course_summary",
        "feedback:resource_summary",
    }
)


def identifier_routes(patterns: object = None, namespaces: tuple = ()) -> dict:
    """Walk URLconf, including non-pk names for course IDs and account IDs."""
    found = {}
    for pattern in patterns if patterns is not None else get_resolver().url_patterns:
        if isinstance(pattern, URLResolver):
            nested = namespaces + ((pattern.namespace,) if pattern.namespace else ())
            if "admin" not in nested:
                found.update(identifier_routes(pattern.url_patterns, nested))
        else:
            keys = tuple(pattern.pattern.regex.groupindex)
            if set(keys) & {"pk", "course_id", "user_id"}:
                found[":".join((*namespaces, pattern.name))] = keys
    return found


def target_url(name: str, keys: tuple, bundle: dict, kind: str = "trainee") -> str:
    """Bind every converter to a real existing object of the intended owner."""
    target = BINDINGS[name]
    if name == "profiles:private_file":
        target = {
            "trainee": "trainee_profile",
            "trainer": "trainer_profile",
            "certificate": "certificate",
        }[kind]
    values = dict.fromkeys(keys, bundle[target].pk)
    if "kind" in values:
        values["kind"] = kind
    if "module_id" in values:
        values["module_id"] = bundle["module"].pk
    return reverse(name, kwargs=values)


def methods_for(name: str) -> tuple:
    """Exercise actual writes for action URLs and both methods for editable forms."""
    if name in STATE_NAMES:
        return ("post",)
    return ("get",) if name in READ_ONLY else ("get", "post")
