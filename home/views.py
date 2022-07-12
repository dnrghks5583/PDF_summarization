from django.http import HttpResponse
from django.shortcuts import render
from .models import Contact, Document
from .kobart import Kobart
from .sts import Sts
from .ptt import save_images, preprocessing, \
    get_clean_text, slicing, set_figure, make_pdf
import os
# Create your views here.

def index(request) :
    return render(request, 'index.html')

def about(request) :
    return render(request, 'about.html')

def contact(request) :
    return render(request, 'contact.html')

def summary(request) :
    return render(request, 'summary.html')

def make_dict(text, summary, imgs) :
    return {'text' : text, 'summary' : summary, 'img' : imgs}

def get_para_list(word, pp) :
    return set([p[0] for p in pp]) if word == '' else set([p[0] for p in pp for text in p[1] if word in text])

def get_output(para_sum, result, string):
    sentences = [string[idx] for idx in result]
    return [(para[0], sentence) for sentence in sentences for para in para_sum if sentence in para[1]]

def make_result(summ) :
    ret = []
    for s in summ : ret.extend([s, '\n'])
    return ret

def init_folders(img_path, media_path) :
    remove_all(  img_path)
    remove_all(media_path)

def remove_all(path) :
    for file in os.listdir(path) : os.remove(path + '/' + file)
    
def get_post(request) :
    img_path = 'final/static/img'
    path     = 'media'
    kobart   = Kobart()
    sts      = Sts()
    
    if request.method == 'POST' :
        text = request.POST['text']
        word = request.POST['word']
        line = int(request.POST['line'])
        sts.set_line(line)

        try :   ## pdf
            pdf       = request.FILES['pdf']
            init_folders(img_path, path)
            doc       = Document()
            doc.title = pdf.name
            doc.pdf   = pdf
            doc.save()
            save_images(path, doc.title)
            
            pp        = preprocessing(path + '/' + pdf.name)
            img_list  = set_figure(pp, img_path)
            para_list = get_para_list(word, pp)
    
            para_sum  = kobart.para_summary(pp, para_list) # 문단별 요약
            string    = [text for texts in para_sum for text in texts[1]]
            
            sts.set_corpus(string)      # sts    
            query     = kobart.summary(''.join(string))
            result    = sts.similarity(query)
            output    = get_output(para_sum, result, string)
            texts     = ' '.join(get_clean_text(path + '/' + pdf.name))
            context   = make_dict(texts, make_result([text[1] for text in output]), os.listdir(img_path))
            make_pdf(output, img_list, 'final/static/pdf/' + 'summary.pdf') 
        except :  ## text
            pp        = slicing(text.replace('\n', ''), 256)
            indices   = [i for i in range(len(pp)) if word in pp[i]]
            temp      = [kobart.summary(pp[idx]) for idx in indices]
            string    = ' '.join(temp)
            sts.set_corpus(temp)
            query     = kobart.summary(string)
            result    = sts.similarity(query)
            result.sort()
            context   = make_dict(text, make_result([temp[idx] for idx in result]), [])   
    else :
        context = make_dict('text', 'summ', [])
    return render(request, 'result.html', context)

def download(request) :
    response = HttpResponse(open('final/static/pdf/summary.pdf', 'rb'), content_type = 'application/pdf')
    response['Content-Disposition'] = 'attachment; filename="summary.pdf"'
    return response

def get_contact(request) :
    if request.method == 'POST' : ## post
        cont      = Contact()
        cont.name = request.POST['name'   ]
        cont.mail = request.POST['email'  ]
        cont.pnum = request.POST['phone'  ]
        cont.msg  = request.POST['message']
        cont.save()
    else :      ## get
        return render(request, 'contact.html')
    return render(request, 'contact.html')