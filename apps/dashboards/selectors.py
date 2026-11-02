"""Expose the read-only dashboard handoffs without importing HTTP controllers."""

from apps.dashboards.admin_selectors import admin_dashboard as admin_dashboard
from apps.dashboards.trainer_selectors import trainer_dashboard as trainer_dashboard
