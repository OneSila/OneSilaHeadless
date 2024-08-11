from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

from django.conf import settings

import os


def stylesheet():
    ''' Override the getSampleStyleSheet, and add own styles'''
    styles = getSampleStyleSheet()
    pdfmetrics.registerFont(TTFont('Arial', os.path.join(settings.STATIC_ROOT, 'fonts/Arial.ttf')))
    styles.add(ParagraphStyle(name='BodyTextCenter', parent=styles['BodyText'], alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='Bold', parent=styles['BodyText'], fontName='Arial'))

    styles['Title'].fontName = 'Arial'
    styles['BodyText'].fontName = 'Arial'
    styles['Bullet'].fontName = 'Arial'
    styles['Heading1'].fontName = 'Arial'
    styles['Heading2'].fontName = 'Arial'
    styles['Heading3'].fontName = 'Arial'
    styles['BodyTextCenter'].fontName = 'Arial'
    return styles


def stylesheet_washinglabels():
    ''' Override the getSampleStyleSheet, and add own styles'''
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='Bold',
        parent=styles['BodyText'],
        fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(
        name='BoldSmall',
        parent=styles['Bold'],
        fontSize=8))
    styles.add(ParagraphStyle(
        name='BoldSmallCenter',
        parent=styles['BoldSmall'],
        alignment=TA_CENTER,
        spaceAfter=4))
    styles.add(ParagraphStyle(
        name='BoldTinyCenter',
        parent=styles['BoldSmallCenter'],
        fontSize=6))
    styles.add(ParagraphStyle(
        name='NormalSmall',
        parent=styles['Normal'],
        fontSize=8))
    styles.add(ParagraphStyle(
        name='NormalSmallCenter',
        parent=styles['NormalSmall'],
        alignment=TA_CENTER))
    return styles
