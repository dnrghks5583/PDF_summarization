from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from operator import itemgetter

import fitz
import os

def fonts(doc, granularity=False):
    """Extracts fonts and their usage in PDF documents.
    :param doc: PDF document to iterate through
    :type doc: <class 'fitz.fitz.Document'>
    :param granularity: also use 'font', 'flags' and 'color' to discriminate text
    :type granularity: bool
    :rtype: [(font_size, count), (font_size, count}], dict
    :return: most used fonts sorted by count, font style information
    """
    styles = {}
    font_counts = {}

    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:  # iterate through the text blocks
            if b['type'] == 0:  # block contains text
                for l in b["lines"]:  # iterate through the text lines
                    for s in l["spans"]:  # iterate through the text spans
                        if granularity:
                            identifier = "{0}_{1}_{2}_{3}".format(s['size'], s['flags'], s['font'], s['color'])
                            styles[identifier] = {'size': s['size'], 'flags': s['flags'], 'font': s['font'],
                                                  'color': s['color']}
                        else:
                            identifier = "{0}".format(s['size'])
                            styles[identifier] = {'size': s['size'], 'font': s['font']}

                        font_counts[identifier] = font_counts.get(identifier, 0) + 1  # count the fonts usage

    font_counts = sorted(font_counts.items(), key=itemgetter(1), reverse=True)

    if len(font_counts) < 1:
        raise ValueError("Zero discriminating fonts found!")

    return font_counts, styles

def font_tags(font_counts, styles):
    """Returns dictionary with font sizes as keys and tags as value.
    :param font_counts: (font_size, count) for all fonts occuring in document
    :type font_counts: list
    :param styles: all styles found in the document
    :type styles: dict
    :rtype: dict
    :return: all element tags based on font-sizes
    """
    p_style = styles[font_counts[0][0]]  # get style for most used font by count (paragraph)
    p_size = p_style['size']  # get the paragraph's size

    # sorting the font sizes high to low, so that we can append the right integer to each tag
    font_sizes = []
    for (font_size, count) in font_counts:
        font_sizes.append(float(font_size))
    font_sizes.sort(reverse=True)

    # aggregating the tags for each font size
    idx = 0
    size_tag = {}
    for size in font_sizes:
        idx += 1
        if size == p_size:
            idx = 0
            size_tag[size] = '<p>'
        if size > p_size:
            size_tag[size] = '<h{0}>'.format(idx)
        elif size < p_size:
            size_tag[size] = '<s{0}>'.format(idx)

    return size_tag

def headers_para(doc, size_tag):
    """Scrapes headers & paragraphs from PDF and return texts with element tags.
    :param doc: PDF document to iterate through
    :type doc: <class 'fitz.fitz.Document'>
    :param size_tag: textual element tags for each size
    :type size_tag: dict
    :rtype: list
    :return: texts with pre-prended element tags
    """
    header_para = []  # list with headers and paragraphs
    first = True  # boolean operator for first header
    previous_s = {}  # previous span

    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:  # iterate through the text blocks
            if b['type'] == 0:  # this block contains text

                # REMEMBER: multiple fonts and sizes are possible IN one block

                block_string = ""  # text found in block
                for l in b["lines"]:  # iterate through the text lines
                    for s in l["spans"]:  # iterate through the text spans
                        if s['text'].strip():  # removing whitespaces:
                            if first:
                                previous_s = s
                                first = False
                                block_string = size_tag[s['size']] + s['text']
                            else:
                                if s['size'] == previous_s['size']:

                                    if block_string and all((c == "|") for c in block_string):
                                        # block_string only contains pipes
                                        block_string = size_tag[s['size']] + s['text']
                                    if block_string == "":
                                        # new block has started, so append size tag
                                        block_string = size_tag[s['size']] + s['text']
                                    else:  # in the same block, so concatenate strings
                                        block_string += " " + s['text']

                                else:
                                    header_para.append(block_string)
                                    block_string = size_tag[s['size']] + s['text']

                                previous_s = s

                    # new block started, indicating with a pipe
                    # block_string += "|"

                header_para.append(block_string)

    return header_para

def istitle(text) :
    if text.count('.') != 1 :
        return False
    numbers = ['I', 'V', 'X', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    
    for num in text.split('.')[0] :
        if num not in numbers :
            return False
    return True

def get_titles(pdf):

    doc = fitz.open(pdf)

    font_counts, styles = fonts(doc, granularity=False)
    size_tag            = font_tags(font_counts, styles)
    elements            = headers_para(doc, size_tag)

    temp   = [element[:4] for element in elements if '<h' in element]
    temp   = list(set(temp))
    temp.sort()
    titles = [' '.join(element[4:].split()) for element in elements if element[:4] == temp[1] if istitle(element[4:])]

    return titles 

def get_text(pdf) :        
    file = extract_pages(pdf)
    return [element.get_text() for page_layout in file for element in page_layout if isinstance(element, LTTextContainer)]

def clean_text(texts) :
    temp = [text.replace('\n', '') for text in texts]
    return [' '.join(t.split()) for t in temp]

def get_clean_text(file) :    # args : path, file ex) 'media', 'name.pdf' return : text (string)
    return clean_text(get_text(file)) 

def slicing(para, c = 512) :
    temp   = []
    string = ''
    for text in para.split('.') :
        if len(string) + len(text) > c :
            temp.append(string)
            string = text + '.'
        else :
            string += text + '.'
    temp.append(string)
    return temp

def paragraph(ct, titles) :
    
    indices = [idx for idx, text in enumerate(ct) if text in titles]
    paras   = []
    for index in range(len(indices)) :
        if index == len(indices) - 1 :
            paras.append(ct[indices[index] : -1])
        else :
            paras.append(ct[indices[index] : indices[index + 1]])
    return paras
            
def preprocessing(file) :
    ct     = get_clean_text(file)
    titles = get_titles(file)
    paras  = paragraph(ct, titles)
    temp   = [' '.join(para) for para in paras if para]
    datas  = [slicing(para) for para in temp]
    return [(idx + 1, data) for idx, data in enumerate(datas)]

def save_images(path, pdf) :
    
    folder    = 'final/static/img/'
    open_file = fitz.open(path + '/' + pdf)
    figure    = '그림 '
    it        = 0
    for i in range(len(open_file)):
        for img in open_file.getPageImageList(i):
            xref = img[0]
            pix  = fitz.Pixmap(open_file, xref)
            if pix.n < 5:       # this is GRAY or RGB
                it += 1
                pix.save(folder + figure + f"{it}.png")
            else:               # CMYK: convert to RGB first
                pix1 = fitz.save(fitz.csRGB, pix)
                it += 1
                pix1.save(folder + figure + f"{it}.png")
                pix1 = None
            pix = None

def set_figure(para, img_path) : 
    # para     = list(para_number, text)
    # img_path = image path (string)
    # return   = list(para_number, list(img_name))
    
    img_list = os.listdir(img_path)
    ret      = {}
    for p in para :
        para_num = p[0]
        texts    = p[1]
        for text in texts :
            for img in img_list :    
                fig_name = img.replace('.png', '')
                if fig_name in text or fig_name.replace('그림', 'figure') in text :
                    if para_num in ret.keys() :
                        ret[para_num].append(fig_name + '.png')
                    else :
                        ret[para_num] = [fig_name + '.png']
    return list(ret.items())

def make_pdf(result, img, path) :
    # para list list(para num, para)
    # img       list(para num, list(img name))
    # para_num  set (para num)
    doc = SimpleDocTemplate(path,
                            pagesize = letter,
                            rightMargin = 72, leftMargin   = 72,
                            topmargin   = 72, bottomMargin = 18)
    styles = getSampleStyleSheet()
    spacer = Spacer(1, 0.25*inch)
    flow = []    
    ## Korean font setting
    FONT_FILE = '%s/Fonts/%s' % (os.environ['WINDIR'], 'BATANG.TTC')
    FONT_NAME = '바탕'
    pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_FILE))
    styles.add(ParagraphStyle(name = "Hangul", fontName = FONT_NAME))
    ##
    for paragraph in result :
        num = paragraph[0]
        flow.append(Paragraph(paragraph[1], style = styles['Hangul']))
        flow.append(spacer)

        for image in img :
            pn = image[0]
            if pn == num :
                for i in image[1] :
                    flow.append(Image('final/static/img/' + i, width = 16*cm, height = 12*cm))
                    flow.append(spacer)

    doc.build(flow)