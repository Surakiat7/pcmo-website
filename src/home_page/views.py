from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from dashboard.models import LoginLog, Map, Map_img


def index(request):
    maps = Map.objects.order_by('id').all()
    places = list()
    for i, m in enumerate(maps):
        r = dict()
        r['id'] = i+1
        r['title'] = m.title
        r['detail'] = m.detail
        r['dep'] = m.store.data['departments']
        r['coords'] = [float(m.latlong.split(',')[0]), float(m.latlong.split(',')[1])]
        r['imgs'] = list()
        imgs = Map_img.objects.order_by("id").filter(map=m)
        for img in imgs:
            r['imgs'].append(img.img.url)
        places.append(r)
    return render(request,'home_page/index.html',{'maps': places})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            log = LoginLog(user=user)
            log.save()
            return redirect('dashboard')
        else:
            messages.error(request, 'ชื่อผู้ใช้และรหัสผ่านของคุณไม่ตรงกัน กรุณาลองอีกครั้ง.')
            return redirect('login')
    return render(request, 'home_page/login.html')