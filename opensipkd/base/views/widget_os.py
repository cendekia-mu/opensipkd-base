from colander import SchemaNode, null, Mapping, Invalid, text_
from deform.widget import Widget, _StrippedString


class DokumenWidget(Widget):
    template = "opensipkd.base:/views/templates/dokumen.pt"
    readonly_template = "opensipkd.base:/views/templates/readonly/dokumen.pt"
    assume_y2k = True

    _pstruct_schema = SchemaNode(
        Mapping(),
        SchemaNode(_StrippedString(), name="jenis"),
        SchemaNode(_StrippedString(), name="year"),
        SchemaNode(_StrippedString(), name="bundle"),
        SchemaNode(_StrippedString(), name="seq"),
    )

    def serialize(self, field, cstruct, **kw):
        if cstruct is null:
            jenis = ""
            year = ""
            bundle = ""
            seq = ""
        else:
            jenis, year, bundle, seq = cstruct.split(".", 3)

        kw.setdefault("jenis", jenis)
        kw.setdefault("year", year)
        kw.setdefault("bundle", bundle)
        kw.setdefault("seq", seq)

        readonly = kw.get("readonly", self.readonly)
        template = readonly and self.readonly_template or self.template
        values = self.get_template_values(field, cstruct, kw)
        return field.renderer(template, **values)

    def deserialize(self, field, pstruct):
        if pstruct is null:
            return null
        else:
            try:
                validated = self._pstruct_schema.deserialize(pstruct)
            except Invalid as exc:
                raise Invalid(field.schema, text_("Invalid pstruct: %s" % exc))
            jenis = validated["jenis"]
            year = validated["year"]
            bundle = validated["bundle"]
            seq = validated["seq"]

            if not year and not bundle and not seq:
                return null

            if self.assume_y2k and len(year) == 2:
                year = "20" + year
            result = ".".join([jenis, year, bundle, seq])

            if not year or not bundle or not seq:
                raise Invalid(field.schema, "No Dokumen tidak lengkap", result)

            return result


class FormulirWidget(Widget):
    template = "opensipkd.base:/views/templates/formulir.pt"
    readonly_template = "opensipkd.base:/views/templates/readonly/formulir.pt"
    assume_y2k = True

    _pstruct_schema = SchemaNode(
        Mapping(),
        SchemaNode(_StrippedString(), name="year"),
        SchemaNode(_StrippedString(), name="bundle"),
        SchemaNode(_StrippedString(), name="seq"),
    )

    def serialize(self, field, cstruct, **kw):
        if cstruct is null:
            year = ""
            bundle = ""
            seq = ""
        else:
            year, bundle, seq = cstruct.split(".", 3)

        kw.setdefault("year", year)
        kw.setdefault("bundle", bundle)
        kw.setdefault("seq", seq)

        readonly = kw.get("readonly", self.readonly)
        template = readonly and self.readonly_template or self.template
        values = self.get_template_values(field, cstruct, kw)
        return field.renderer(template, **values)

    def deserialize(self, field, pstruct):
        if pstruct is null:
            return null
        else:
            try:
                validated = self._pstruct_schema.deserialize(pstruct)
            except Invalid as exc:
                raise Invalid(field.schema, text_("Invalid pstruct: %s" % exc))
            year = validated["year"]
            bundle = validated["bundle"]
            seq = validated["seq"]

            if not year and not bundle and not seq:
                return null

            if self.assume_y2k and len(year) == 2:
                year = "20" + year
            result = ".".join([year, bundle, seq])

            if not year or not bundle or not seq:
                raise Invalid(field.schema, "No Dokumen tidak lengkap", result)

            return result


class BlokKavNoWidget(Widget):
    template = "opensipkd.base:/views/templates/blok_kav_no.pt"
    readonly_template = "opensipkd.base:/views/templates/readonly/blok_kav_no.pt"

    _pstruct_schema = SchemaNode(
        Mapping(),
        SchemaNode(_StrippedString(), name="blok_kav_no"),
        SchemaNode(_StrippedString(), name="rt"),
        SchemaNode(_StrippedString(), name="rw")
    )

    def serialize(self, field, cstruct, **kw):
        if cstruct is null:
            blok_kav_no = ""
            rt = "000"
            rw = "00"
        else:
            blok_kav_no, rt, rw = cstruct.split("|", 3)

        kw.setdefault("blok_kav_no", blok_kav_no)
        kw.setdefault("rt", rt)
        kw.setdefault("rw", rw)

        readonly = kw.get("readonly", self.readonly)
        template = readonly and self.readonly_template or self.template
        values = self.get_template_values(field, cstruct, kw)
        return field.renderer(template, **values)

    def deserialize(self, field, pstruct):
        if pstruct is null:
            return null
        else:
            try:
                validated = self._pstruct_schema.deserialize(pstruct)
            except Invalid as exc:
                raise Invalid(field.schema, text_("Invalid pstruct: %s" % exc))
            blok_kav_no = validated["blok_kav_no"]
            rt = validated["rt"]
            rw = validated["rw"]

            if not blok_kav_no and not rt and not rw:
                return null

            result = "|".join([blok_kav_no, rt, rw])

            if not blok_kav_no or not rt or not rw:
                raise Invalid(field.schema, "Blok Kav No RT/RW tidak lengkap", result)

            return result
