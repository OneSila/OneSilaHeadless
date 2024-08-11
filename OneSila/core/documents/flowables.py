from reportlab.graphics.barcode.eanbc import Ean13BarcodeWidget
from reportlab.platypus import Flowable
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF


class EAN13BarCode(Flowable):
    # Based on https://stackoverflow.com/questions/18569682/use-qrcodewidget-or-plotarea-with-platypus
    # and https://stackoverflow.com/questions/38894523/apply-alignments-on-reportlab-simpledoctemplate-to-append-multiple-barcodes-in-n
    def __init__(self, value="1234567890", ratio=1):
        # init and store rendering value
        Flowable.__init__(self)
        self.value = value
        self.ratio = ratio

    def wrap(self, availWidth, availHeight):
        # Make the barcode fill the width while maintaining the ratio
        self.width = availWidth
        self.height = self.ratio * availWidth
        return self.width, self.height

    def draw(self):
        # Flowable canvas
        bar_code = Ean13BarcodeWidget(value=self.value)
        bounds = bar_code.getBounds()
        bar_width = bounds[2] - bounds[0]
        bar_height = bounds[3] - bounds[1]
        w = float(self.width)
        h = float(self.height)
        d = Drawing(w, h, transform=[w / bar_width, 0, 0, h / bar_height, 0, 0])
        d.add(bar_code)
        renderPDF.draw(d, self.canv, 0, 0)
