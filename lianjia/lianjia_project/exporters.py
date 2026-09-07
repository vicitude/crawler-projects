from scrapy.exporters import CsvItemExporter


class Utf8SigCsvItemExporter(CsvItemExporter):
    """固定字段顺序，并用 Excel 友好的 UTF-8 BOM 编码输出。"""

    def __init__(self, file, **kwargs):
        kwargs.setdefault("encoding", "utf-8-sig")
        kwargs.setdefault("include_headers_line", True)
        kwargs.setdefault(
            "fields_to_export",
            [
                "title",
                "house_tag",
                "total_price",
                "unit_price",
                "community_name",
                "region_name",
                "layout",
                "area",
                "orientation",
                "decorate_status",
                "floor",
                "building_type",
                "is_near_subway",
                "tax_free_type",
                "is_has_key",
            ],
        )
        super().__init__(file, **kwargs)
