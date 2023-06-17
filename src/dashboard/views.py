from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect, reverse
import pandas as pd
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Store, LoginLog, Utility, Map, Map_img
from .forms import MapUpload
from pprint import pprint
import traceback
from datetime import timedelta, date
from django.utils import timezone
from io import BytesIO
from django.http import HttpResponse
# Create your views here.


def check_user(user: User):
    return not user.is_staff and not user.is_superuser


def check_staff(user: User):
    return user.is_staff


def check_admin(user: User):
    return user.is_superuser


@login_required
def dashboard(request):
    if request.user.is_superuser:
        return redirect('manageStore')
    elif request.user.is_staff:
        return redirect('staff')
    elif not request.user.is_staff and not request.user.is_superuser:
        return redirect('user')
    else:
        return redirect('/')


@login_required
@user_passes_test(check_admin, login_url='/dashboard')
def addData(request):
    return render(request, 'dashboard/addData.html')

columns_change_type = [
    "Maintenance_id",
    "Maintenance_Number",
    "Insurance_id",
    "Insurance_Number",
    "Support_id_ST",
    "Support_Number_ST",
    "Support_id_PCM",
    "Support_Number_PCM",
    
]
columns_change_date = [
    'contract_start',
    'contract_end',
    'Insurance_Timestamp',
    'SupportTimestamp_ST',
    'Support_Timestamp_PCM',
    'Maintenance_Timestamp',

]

@login_required 
@user_passes_test(check_admin, login_url='/dashboard')
def addExcel(request):
    if request.method == 'POST':
        try:
            data = request.FILES['myfile'].read()
            df = pd.read_excel(data).fillna('-')
            del df["No"]
            excel_dict = df.to_dict(orient='records')
            for s in excel_dict:
                for i in columns_change_date:
                    if isinstance(s[i], str):
                        continue
                    s[i] = s[i].date()
                    if s[i] < (date.today() - timedelta(days=3650)): s[i] = s[i].replace(year=s[i].year+57)
                for i in columns_change_type:
                    try:
                        s[i] = int(s[i])
                    except:
                        continue
                store, created = Store.objects.get_or_create(data__Type=s['Type'], data__departments=s['departments'], data__License_name=s['License_name'], defaults={'data': s})
                if not created: store.data = s
                store.modify_by = request.user
                store.save()
        except:
            traceback.print_exc()
            messages.error(request, "เพิ่มข้อมูลไม่สำเร็จ")
            return redirect('manageStore')
        messages.success(request, "เพิ่มข้อมูล excel เสร็จสิ้น")
        return redirect('manageStore')
    
@login_required
@user_passes_test(check_admin, login_url='/dashboard')
def addDataForm(request):
    if request.method == 'POST':
        try:
            form_dict = dict()
            for i in request.POST:
                if request.POST[i] == "":
                    form_dict.update({f"{i}":"-"})
                else:
                    try:
                        if i == "PhoneNumber":
                            raise TypeError
                        ii = int(request.POST[i])
                    except:
                        ii = request.POST[i]
                    form_dict.update({f"{i}": ii})
            del form_dict['csrfmiddlewaretoken']
            store = Store(data=form_dict, modify_by=request.user)
            store.save()
        except:
            pass
        messages.success(request, f'เพิ่ม {store.data["Type"]} สำเร็จ')
        return redirect('manageStore')



# map fuctions start
@login_required
@user_passes_test(check_admin, login_url='/dashboard')
def managePlace(request):
    stores = list(Store.objects.order_by('-last_modify').all())
    for i in stores:
        i.isdanger = False
        if not hasattr(i, 'map'): i.isdanger = True
    stores.sort(key=lambda x : not hasattr(x, 'map'), reverse=True)
    return render(request, 'dashboard/managePlace.html',{'stores': stores})


@login_required
@user_passes_test(check_admin, login_url='/dashboard')
def map_info(request, id:int):
    store = Store.objects.get(id=id)
    if request.method == 'POST':
        title = request.POST['title']
        latlong = request.POST['latlong']
        detail = request.POST['detail']
        map, created = Map.objects.get_or_create(store=store)
        map.title = title
        map.latlong = latlong
        map.detail = detail
        map.save()
        return redirect('mapinfo', id=id)
    else:
        form = MapUpload()
        print(form)
        isexist = True if Map.objects.filter(store=store) else False
        if isexist:
            map = Map.objects.get(store=store)
            imgs = Map_img.objects.order_by('id').filter(map=map)
        else:
            map = dict()
            imgs = list()
    return render(request ,'dashboard/info/map_info.html', {'form': form, 'store': store, "isexist": isexist, "map": map, 'imgs': imgs})

@login_required
@user_passes_test(check_admin, login_url='/dashboard')
def img_upload(request, id:int):
    if request.method == 'POST':
        form = MapUpload(request.POST, request.FILES)
        files = request.FILES.getlist('img')
        map = Map.objects.get(store=Store.objects.get(id=id))
        if form.is_valid():
            for img in files:
                print(img)
                obj = Map_img(map=map,img=img)
                obj.save()
        return redirect('mapinfo', id=id)

@login_required
@user_passes_test(check_admin, login_url='/dashboard')
def delete_img(request, storeid:int,id:int):
    img = Map_img.objects.get(id=id)
    img.delete()
    return redirect('mapinfo', id=storeid)
    

# map fuctions end


@login_required
@user_passes_test(check_admin, login_url='/dashboard')
def addData2(request):
    stores = Store.objects.order_by("data__Type").all()
    if request.method == "POST":
        return redirect(reverse("addUtility")+f"?billing_month={request.POST['startDate']}")
    return render(request, 'dashboard/addData2.html', {'stores': stores})

@login_required
@user_passes_test(check_admin, login_url='/dashboard')
def addUtility(request):
    form_date = date.fromisoformat(f"{request.GET.get('billing_month')}-01")
    # print(form_date)
    stores = Store.objects.order_by('id').all()
    billing_table = []
    for i in stores:
        obj, created = Utility.objects.get_or_create(date=form_date, store=i)
        obj.save()
        billing_table.append(obj)
    return render(request, 'dashboard/addUtility.html', {"billing_month":request.GET.get('billing_month'), "form_date": form_date, "billing_table": billing_table})

@login_required
@user_passes_test(check_admin, login_url='/dashboard')
def addUtilityPost(request):
    if request.method == "POST":
        form_date = date.fromisoformat(f"{request.POST['startDate']}-01")
        # print(form_date)
        for i in request.POST:
            if i == 'startDate' or i == 'csrfmiddlewaretoken':
                continue
            # print(i)
            id = int(i.split('-')[0])
            coll = i.split('-')[1]
            obj, created = Utility.objects.get_or_create(
                id=id
            )
            if coll == 'water':
                obj.water = float(request.POST[i])
            elif coll == 'electric':
                obj.electric = float(request.POST[i])
            else:
                obj.wash = float(request.POST[i])
            obj.save()
        messages.success(request, f"บันทึก {request.POST['startDate']} เสร็จสิ้น")
        return redirect('addData2')
        
@login_required
@user_passes_test(check_admin, login_url='/dashboard')
def showLicense(request):
    licenses = Store.objects.all()
    licenses_data = list()
    for i in licenses:
        r = dict()
        r.update(i.data)
        r["isdanger"] = False
        if i.data["contract_start"] == "-" or i.data["contract_end"] == "-": continue
        if date.fromisoformat(i.data["contract_end"]) <= date.today():
            r["isdanger"] = True
        if (date.fromisoformat(i.data["contract_end"]) - date.fromisoformat(i.data["contract_start"])) > timedelta(days=360):
            if (date.fromisoformat(i.data["contract_end"]) - date.today()) < timedelta(days=124):
                licenses_data.append(r)
        else:
            licenses_data.append(r)
    licenses_data.sort(key=lambda r: date.fromisoformat(r["contract_end"]))
    return render(request, 'dashboard/showLicense.html',{"license":licenses_data})


@login_required
@user_passes_test(check_admin, login_url='/dashboard')
def login_log(request):
    week = LoginLog.objects.filter(timestamp__gte=timezone.now()-timedelta(weeks=1)).count()
    month = LoginLog.objects.filter(timestamp__gte=timezone.now()-timedelta(days=30)).count()
    year = LoginLog.objects.filter(timestamp__gte=timezone.now()-timedelta(days=365)).count()
    return render(request, 'dashboard/login_log.html', {"week": week, 'year': year, 'month': month})


# store manament function start

@login_required
@user_passes_test(check_admin, login_url='/dashboard')
def manageStore(request):
    stores = list(Store.objects.order_by('-last_modify').all())
    stores.sort(key=lambda x : not x.owner, reverse=True)
    return render(request, 'dashboard/manageStore.html',{'stores': stores})

@login_required
@user_passes_test(check_admin, login_url='/dashboard')
def edit_store(request, id: int):
    if request.method == 'POST':
        try:
            form_dict = dict()
            for i in request.POST:
                if request.POST[i] == "":
                    form_dict.update({f"{i}":"-"})
                else:
                    try:
                        if i == "PhoneNumber":
                            raise TypeError
                        ii = int(request.POST[i])
                    except:
                        ii = request.POST[i]
                    form_dict.update({f"{i}": ii})
            del form_dict['csrfmiddlewaretoken']
            store = Store.objects.get(id=id)
            store.data = form_dict
            store.modify_by = request.user
            store.save()
        except:
            pass
        messages.success(request, f'แก้ไข {store.data["Type"]} สำเร็จ')
        return redirect('manageStore')
        
@login_required
@user_passes_test(check_admin, login_url='/dashboard')
def export_store(request):
    stores = Store.objects.order_by('id').all()
    data = list()
    for i in stores:
        data.append((
            i.data["Type"],
            i.data["departments"],
            i.data["License_name"],
            i.data["Address"],
            i.data["PhoneNumber"],
            i.data['contract_period'],
            i.data["contract_start"] if i.data["contract_start"] == "-" else date.fromisoformat(i.data["contract_start"]),
            i.data["contract_end"] if i.data["contract_end"] == "-" else date.fromisoformat(i.data['contract_end']),
            i.data['Area_maintenance'],
            i.data['Maintenance_id'],
            i.data['Maintenance_Number'],
            i.data["Maintenance_Timestamp"] if i.data["Maintenance_Timestamp"] == "-" else date.fromisoformat(i.data['Maintenance_Timestamp']),
            i.data['contract_insurance'],
            i.data['Insurance_id'],
            i.data['Insurance_Number'],
            i.data["Insurance_Timestamp"] if i.data["Insurance_Timestamp"] == "-" else date.fromisoformat(i.data['Insurance_Timestamp']),
            i.data['Support_ST'],
            i.data['Support_id_ST'],
            i.data['Support_Number_ST'],
            i.data["SupportTimestamp_ST"] if i.data["SupportTimestamp_ST"] == "-" else date.fromisoformat(i.data['SupportTimestamp_ST']) ,
            i.data['Support_PCM'],
            i.data['Support_id_PCM'],
            i.data['Support_Number_PCM'],
            i.data["Support_Timestamp_PCM"] if i.data["Support_Timestamp_PCM"] == "-" else date.fromisoformat(i.data['Support_Timestamp_PCM']),
            i.data['Note']
        ))
    df = pd.DataFrame.from_records(data, columns=['ประเภทกิจการ', 'คณะ/หน่วยงาน/สำนักงาน', 'ชื่อผู้ได้รับสิทธิ์', 'ที่อยู่', 'หมายเลขโทรศัพท์', 'ระยะเวลาสัญญา', 'เริ่มสัญญา', 'สิ้นสุดสัญญา', 'อัตราค่าบำรุงพื้นที่(บาท/ปี)', 'ใบเสร็จเล่มที่', 'ใบเสร็จเลขที่', 'ใบเสร็จลงวันที่', 'ค่าประกันสัญญา(บาท)', 'ใบเสร็จเล่มที่', 'ใบเสร็จเลขที่', 'ใบเสร็จลงวันที่', 'สนับสนุนเป็นทุนการศึกษาแก่นักศึกษา(บาท)', 'ใบเสร็จของเงินบริจาคเล่มที่', 'ใบเสร็จของเงินบริจาคเลขที่', 'ใบเสร็จของเงินบริจาคลงวันที่', 'สนับสนุนสำนักบริหารทรัพย์สินฯ(บาท)', 'ใบเสร็จของเงินบริจาคเล่มที่', 'ใบเสร็จของเงินบริจาคเลขที่', 'ใบเสร็จของเงินบริจาคลงวันที่', 'หมายเหตุ'])
    with BytesIO() as b:
        writer = pd.ExcelWriter(b, engine='openpyxl')
        df.to_excel(writer, sheet_name='Contract', index=False)
        writer.save()
        today = date.today()
        filename = f'contract_export_{str(today)}.xlsx'
        response = HttpResponse(
            b.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename={filename}'
    return response

@login_required
@user_passes_test(check_admin, login_url='/dashboard')
def store_info(request, id:int):
    store = Store.objects.get(id=id)
    electric = Utility.objects.order_by('-date').filter(electric__gt=0.0, store=store)
    water = Utility.objects.order_by('-date').filter(water__gt=0.0, store=store)
    wash = Utility.objects.order_by('-date').filter(wash__gt=0.0, store=store)
    users = User.objects.order_by('username').filter(is_staff=False, is_superuser=False)
    return render(request, 'dashboard/info/store_info.html', {'store': store, 'water': water, 'wash': wash, 'electric': electric, "users": users})

@login_required
@user_passes_test(check_admin, login_url='/dashboard')
def save_store_owner(request, id: int):
    if request.method == "POST":
        store = Store.objects.get(id=int(id))
        ownerid = int(request.POST['owner'])
        user = User.objects.get(id=ownerid)
        store.owner = user
        store.save()
        messages.success(request, f'ผูกผู้ใช้ {user.username} กับ {store.data["Type"]} เสร็จสิ้น')
        return redirect('manageStore')


@login_required
@user_passes_test(check_admin, login_url='/dashboard')
def delete_store(request, id: int):
    if request.method == 'POST':
        store = Store.objects.get(id=id)
        store.delete()
        messages.error(request, f"ลบ {store.data['Type']} เสร็จสิ้น")
        return redirect('manageStore')


# user manament function start

@login_required
@user_passes_test(check_admin, login_url='/dashboard')
def manageUser(request):
    if request.method == "POST":
        username = request.POST['username']
        if User.objects.filter(username=username):
            messages.error(request, f'ชื่อผู้ใช้ {username} มีในระบบอยู่แล้ว')
            return render(request, 'dashboard/manageUser.html')
        password = request.POST['password']
        if len(password) <= 4:
            messages.error(request, f'รหัสผ่านต้องมากกว่า 4 ตัว')
            return render(request, 'dashboard/manageUser.html')
        name = request.POST['name']
        surname = request.POST['surname']
        userlevel = int(request.POST['userlevel'])
        # print(name,surname,username,password, userlevel)
        user = User.objects.create_user(username=username, password=password)
        user.first_name = name
        user.last_name = surname
        if userlevel == 2:
            user.is_staff = True
        elif userlevel == 3:
            user.is_superuser = True
        user.save()
        messages.success(request, f'เพิ่มผู้ใช้ {username} สำเร็จ')
        return redirect('manageUser')
    userlist = User.objects.order_by('username').all()
    return render(request, 'dashboard/manageUser.html', {'userlist': userlist})



@login_required
@user_passes_test(check_admin, login_url='/dashboard')
def user_info(request, id: int):
    user = User.objects.get(id=id)
    login_his = LoginLog.objects.order_by('-timestamp').filter(user=user)
    return render(request, 'dashboard/info/user_info.html', {'user': user, "history": login_his})


@login_required
@user_passes_test(check_admin, login_url='/dashboard')
def export_user(request):
    users = User.objects.order_by('username').filter(is_staff=False, is_superuser=False)
    data = list()
    for i in users:
        data.append((i.username, i.first_name, i.last_name))
    df = pd.DataFrame.from_records(data, columns=['ชื่อผู้ใช้', 'ชื่อ', 'สกุล'])
    with BytesIO() as b:
        writer = pd.ExcelWriter(b, engine='openpyxl')
        df.to_excel(writer, sheet_name='User', index=False)
        writer.save()
        today = date.today()
        filename = f'user_export_{str(today)}.xlsx'
        response = HttpResponse(
            b.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename={filename}'
    return response


@login_required
@user_passes_test(check_admin, login_url='/dashboard')
def edit_user(request, id: int):
    if request.method == 'POST':
        user = User.objects.get(id=id)
        fname = request.POST['fname']
        lname = request.POST['lname']
        user.first_name = fname
        user.last_name = lname
        user.save()
        messages.success(request, f"แก้ไขข้อมูลผู้ใช้ {user.username} เสร็จสิ้น")
        return redirect('manageUser')

@login_required
@user_passes_test(check_admin, login_url='/dashboard')
def change_password(request, id: int):
    if request.method == 'POST':
        user = User.objects.get(id=id)
        newpass = request.POST['password']
        user.set_password(newpass)
        user.save()
        messages.success(request, f"เปลี่ยนรหัสผ่านผู้ใช้ {user.username} เสร็จสิ้น")
        return redirect('manageUser')

@login_required
@user_passes_test(check_admin, login_url='/dashboard')
def delete_user(request, id: int):
    if request.method == 'POST':
        user = User.objects.get(id=id)
        user.delete()
        messages.error(request, f"ลบผู้ใช้ {user.username} เสร็จสิ้น")
        return redirect('manageUser')

# end admin def


# staff user
@login_required
@user_passes_test(check_staff, login_url='/dashboard')
def staff(request):
    stores = Store.objects.order_by('-last_modify').all()
    # pprint(stores)
    return render(request, 'dashboard/staff.html',{'stores': stores})

# staff store info
@login_required
@user_passes_test(check_staff, login_url='/dashboard')
def staff_store_info(request, id:int):
    store = Store.objects.get(id=id)
    electric = Utility.objects.order_by('-date').filter(electric__gt=0.0, store=store)
    water = Utility.objects.order_by('-date').filter(water__gt=0.0, store=store)
    wash = Utility.objects.order_by('-date').filter(wash__gt=0.0, store=store)
    return render(request, 'dashboard/info/staff_info.html', {'store': store, 'water': water, 'wash': wash, 'electric': electric})



# store user
@login_required
@user_passes_test(check_user, login_url='/dashboard')
def user(request):
    stores = Store.objects.order_by('id').filter(owner=request.user)
    return render(request, 'dashboard/user.html', {"stores": stores})

@login_required
@user_passes_test(check_user, login_url='/dashboard')
def user_utility(request):
    stores = Store.objects.order_by('id').filter(owner=request.user)
    res_stores = list()
    for i in stores:
        i.electric = Utility.objects.order_by('-date').filter(electric__gt=0.0, store=i)
        i.water = Utility.objects.order_by('-date').filter(water__gt=0.0, store=i)
        i.wash = Utility.objects.order_by('-date').filter(wash__gt=0.0, store=i)
    pprint(stores)
    return render(request, 'dashboard/user/userUtility.html', {"stores": stores})

