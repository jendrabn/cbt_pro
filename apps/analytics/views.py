import csv
from io import BytesIO
from urllib.parse import urlencode

from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView
from openpyxl import Workbook

from apps.core.mixins import RoleRequiredMixin

from .services import (
    REPORT_COLUMNS,
    build_chart_data,
    build_report_rows,
    calculate_comparison_metrics,
    calculate_summary_metrics,
    get_filter_options,
    get_filtered_exams,
    parse_analytics_filters,
)


def _format_filename_timestamp():
    return timezone.localtime().strftime("%Y%m%d_%H%M%S")


def _build_query_string_without_page(request):
    querydict = request.GET.copy()
    querydict.pop("page", None)
    querydict.pop("columns", None)
    querydict.pop("columns_param", None)
    return querydict.urlencode()


def _csv_export(rows, export_columns):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="analytics_report_{_format_filename_timestamp()}.csv"'
    response.write("\ufeff")

    column_map = dict(REPORT_COLUMNS)
    writer = csv.writer(response)
    writer.writerow([column_map[col] for col in export_columns])

    for row in rows:
        writer.writerow(
            [
                row[col].strftime("%d-%m-%Y %H:%M") if hasattr(row[col], "strftime") else row[col]
                for col in export_columns
            ]
        )
    return response


def _xlsx_export(rows, export_columns):
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Laporan Analitik"

    column_map = dict(REPORT_COLUMNS)
    worksheet.append([column_map[col] for col in export_columns])

    for row in rows:
        worksheet.append(
            [
                row[col].strftime("%d-%m-%Y %H:%M") if hasattr(row[col], "strftime") else row[col]
                for col in export_columns
            ]
        )

    buffer = BytesIO()
    workbook.save(buffer)
    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="analytics_report_{_format_filename_timestamp()}.xlsx"'
    return response


class AnalyticsAdminBaseView(RoleRequiredMixin):
    required_role = "admin"
    permission_denied_message = "Hanya admin yang dapat mengakses Analitik & Laporan."


class AdminAnalyticsView(AnalyticsAdminBaseView, TemplateView):
    template_name = "analytics/admin_analytics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filters = parse_analytics_filters(self.request)
        exams_qs = get_filtered_exams(filters)
        summary = calculate_summary_metrics(exams_qs, filters)
        comparison = calculate_comparison_metrics(filters)
        chart_data = build_chart_data(exams_qs, filters)
        report_rows = build_report_rows(exams_qs)[:10]
        options = get_filter_options()

        query_string = _build_query_string_without_page(self.request)
        export_base = f"{reverse('export_analytics')}?{query_string}" if query_string else reverse("export_analytics")
        separator = "&" if query_string else "?"
        export_csv_url = f"{export_base}{separator}format=csv"
        export_xlsx_url = f"{export_base}{separator}format=xlsx"
        reports_url = f"{reverse('system_reports')}?{query_string}" if query_string else reverse("system_reports")

        context.update(
            {
                "filters": filters,
                "subjects": options["subjects"],
                "classes": options["classes"],
                "exam_types": options["exam_types"],
                "summary": summary,
                "comparison": comparison,
                "report_rows": report_rows,
                "query_string": query_string,
                "export_csv_url": export_csv_url,
                "export_xlsx_url": export_xlsx_url,
                "reports_url": reports_url,
                "chart_data": chart_data,
            }
        )
        return context


class SystemReportsView(AnalyticsAdminBaseView, TemplateView):
    template_name = "analytics/reports.html"
    paginate_by = 15

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filters = parse_analytics_filters(self.request)
        exams_qs = get_filtered_exams(filters)
        report_rows = build_report_rows(exams_qs)
        options = get_filter_options()

        paginator = Paginator(report_rows, self.paginate_by)
        page_obj = paginator.get_page(self.request.GET.get("page"))

        querydict = self.request.GET.copy()
        querydict.pop("page", None)
        querydict.pop("columns", None)
        querydict.pop("columns_param", None)
        query_string = querydict.urlencode()
        export_base = f"{reverse('export_analytics')}?{query_string}" if query_string else reverse("export_analytics")
        separator = "&" if query_string else "?"

        context.update(
            {
                "filters": filters,
                "subjects": options["subjects"],
                "classes": options["classes"],
                "exam_types": options["exam_types"],
                "report_columns": REPORT_COLUMNS,
                "rows": page_obj.object_list,
                "page_obj": page_obj,
                "is_paginated": page_obj.has_other_pages(),
                "paginator": paginator,
                "query_string": query_string,
                "export_csv_url": f"{export_base}{separator}format=csv",
                "export_xlsx_url": f"{export_base}{separator}format=xlsx",
                "analytics_url": f"{reverse('admin_analytics')}?{query_string}" if query_string else reverse("admin_analytics"),
            }
        )
        return context


class ExportAnalyticsView(AnalyticsAdminBaseView, View):
    def get(self, request):
        filters = parse_analytics_filters(request)
        exams_qs = get_filtered_exams(filters)
        rows = build_report_rows(exams_qs)
        if not rows:
            messages.warning(request, "Tidak ada data laporan untuk diekspor.")
            reports_qs = urlencode(request.GET, doseq=True)
            target = reverse("system_reports")
            return redirect(f"{target}?{reports_qs}" if reports_qs else target)

        export_columns = [key for key, _ in REPORT_COLUMNS]
        export_format = (request.GET.get("format") or "csv").lower()

        if export_format == "xlsx":
            return _xlsx_export(rows, export_columns)
        return _csv_export(rows, export_columns)
