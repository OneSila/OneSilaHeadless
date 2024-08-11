from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.graphics.barcode import eanbc
from reportlab.graphics.shapes import Drawing, Line
from reportlab.graphics import renderPDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, PageBreak, Spacer, Image
from reportlab.lib import colors
from reportlab.graphics.barcode.eanbc import Ean13BarcodeWidget
from reportlab.platypus import Flowable
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from .stylesheets import stylesheet

from io import BytesIO

from django.conf import settings

import textwrap
import os


class OneSilaBaseDocument:
    def __init__(self, page_number=True):
        self.buffer = BytesIO()
        self.elements = []
        self.styles = stylesheet()
        self.margin = 20 * mm
        self.page_number = page_number
        self.doc = SimpleDocTemplate(self.buffer,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=50 * mm,
            bottomMargin=self.margin,
            pagesize=A4)

    # def _add_letterhead(self, canvas, doc):
    #     ''' add letterhead to the page'''
    #     # Save the state of our canvas so we can draw on it
    #     canvas.saveState()
    #     styles = stylesheet()

    #     filename = os.path.join(settings.STATIC_ROOT, 'letterheads/letterhead 2021.jpg')

    #     canvas.drawImage(filename, 0, 0, *A4)

    #     # Footer
    #     if self.page_number:
    #         w = doc.width / 2.0
    #         h = doc.bottomMargin * 2.0
    #         page_num = Paragraph('Page {}'.format(canvas.getPageNumber()), styles['BodyTextCenter'])
    #         w, h = page_num.wrap(doc.width, doc.bottomMargin)
    #         page_num.drawOn(canvas, doc.leftMargin, h)

    #     # Release the canvas
    #     canvas.restoreState()

    def add_invoice_delivery_headers(self, invoice_from, invoice_to, deliver_to):
        # table_data = [
        #     ['', 'Invoice To', 'Deliver To', ''],
        #     ['', invoice_to, deliver_to, ''],
        # ]
        # self.add_table(table_data, [0.15, 0.35, 0.35, 0.15], line_under_header_row=False)

        table_data = [
            ['Invoice From', 'Invoice To', 'Deliver To'],
            [invoice_from, invoice_to, deliver_to],
        ]
        self.add_table(table_data, [0.33, 0.33, 0.33], line_under_header_row=False)
        self.add_vertical_space(10)

    def add_text(self, content, style):
        ''' expects content and a style that is present in the default stylesheet'''
        self.elements.append(Paragraph(content.replace('\n', "<br></br>"), self.styles[style]))

    def add_title(self, content):
        ''' add a title to a page '''
        self.add_text(content, 'Title')

    def add_heading(self, content):
        '''adds a heading2'''
        self.add_text(content, 'Heading2')

    def add_paragraph(self, content):
        ''' add a piece of body/paragraph to a page '''
        self.add_text(content, 'BodyText')

    def add_table(self, table_data, table_widths, bold_header_row=True, line_under_header_row=True,
            box_line=False, row_line=False):
        ''' expects:
        :param table_data: a list of lists for each row
        :param table_widths: a list of widths for each columns in pct ex: [0.4, 0.4, 0.2]
        '''
        table_width = self.doc.width - self.margin
        num_cols = len(table_widths)

        final_table_data = []
        for row in table_data:
            processed_row = []

            if table_data.index(row) is 0 and bold_header_row:
                column_style = self.styles['Bold']
            else:
                column_style = self.styles['BodyText']

            for cell in row:
                if isinstance(cell, Image):
                    processed_row.append(cell)
                else:
                    processed_row.append(Paragraph(str(cell), column_style))

            final_table_data.append(processed_row)

        final_table_widths = []
        for width in table_widths:
            final_table_widths.append(width * table_width)

        table = Table(final_table_data, colWidths=final_table_widths)
        table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP')  # Align cells to top
        ]))

        if line_under_header_row:
            table.setStyle(TableStyle([
                ('LINEBELOW', (0, 0), (num_cols, 0), 1, colors.black),  # Add line below headers
                ('VALIGN', (0, 0), (-1, -1), 'TOP')  # Align cells to top
            ]))
        if box_line:
            table.setStyle(TableStyle([
                ('LINEBELOW', (0, 0), (num_cols, 0), 1, colors.black),
                ('LINEABOVE', (0, 0), (num_cols, 0), 1, colors.black),
                ('LINEBEFORE', (0, 0), (num_cols, 0), 1, colors.black),
                ('LINEAFTER', (0, 0), (num_cols, 0), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP')  # Align cells to top
            ]))
        if row_line:
            table.setStyle(TableStyle([
                ('LINEBELOW', (0, 1), (-1, -1), 1, colors.black),
                ('LINEBELOW', (0, 1), (-1, -1), 1, colors.lightgrey),
                ('VALIGN', (0, 0), (-1, -1), 'BOTTOM')  # Align cells to top
            ]))

        self.elements.append(table)

    def add_image(self, path, width, aspect_ratio):
        '''add image to doc. Expects:
        :param path: path to image
        :param width: with in pct to doc width, ex: 0.5
        '''
        width = width * self.doc.width
        height = width * aspect_ratio
        self.elements.append(Image(path, width, height))

    def add_vertical_space(self, height_in_mm):
        self.elements.append(Spacer(width=0, height=height_in_mm * mm))

    def add_page_break(self):
        self.elements.append(PageBreak())

    def print_document(self):
        # self.doc.build(self.elements, onFirstPage=self._add_letterhead, onLaterPages=self._add_letterhead)
        self.doc.build(self.elements)
        pdf = self.buffer.getvalue()
        self.buffer.close()
        return pdf


class ImageTable:
    def __init__(self, number_of_columns, page_width):
        self.number_of_columns = number_of_columns
        self.page_width = page_width
        self.image_list = []

    def add_image(self, path, aspect_ratio):
        width = self.page_width / self.number_of_columns
        height = width * aspect_ratio
        img_instance = Image(path, width=width, height=height)
        self.image_list.append(img_instance)

    def return_table_data(self):
        table_data = [self.image_list[i:i + self.number_of_columns] for i in xrange(0, len(self.image_list), self.number_of_columns)]
        return table_data
