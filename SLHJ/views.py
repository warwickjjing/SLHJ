from distutils.log import error
from pickle import TRUE
from re import M
from ssl import AlertDescription
from django.http import Http404, JsonResponse
# from jinja2 import Undefined
import requests, bs4
import pandas as pd
from lxml import html
from urllib.request import Request, urlopen
from urllib.parse import urlencode, quote_plus, unquote
from django.shortcuts import render, redirect
from SLHJ.models import User, Vacation, Vacation_reserve, Vacation_review, Vacation_image
from SLHJ.models import Hotel, Hotel_room, Hotel_review, Hotel_reserve, Hotel_image
from datetime import datetime
import datetime
import json
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.db.models import Q
import json
import os
import mimetypes
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import FileResponse
import time
from django.views.decorators.csrf import csrf_exempt
import re
import random
import functools

def main(request):

    vacation_imgs = []
    hotel_imgs = []

    if request.method == 'GET':        
        start_date = request.session.get('start_date')
        end_date = request.session.get('end_date')
        hotel_reserve_people = request.session.get('hotel_reserve_people')
        vacation_reserve_people = request.session.get('vacation_reserve_people', 1)

        if not(start_date or end_date or hotel_reserve_people or vacation_reserve_people):
            del request.session['SIGUN_NM']
            del request.session['start_date']
            del request.session['end_date']
            del request.session['hotel_reserve_people']
            del request.session['vacation_reserve_people']
            del request.session['vacation_date']
        
        hotel_places = Hotel.objects.all().values('SIGUN_NM').distinct()
        vacation_places = Vacation.objects.all().values('SIGUN_NM').distinct()
        recommand_vacations = Vacation.objects.all().order_by('-vacation_rate')[:4]
        recommand_hotels = Hotel.objects.all().order_by('-hotel_rate')[:4]

        # ?????? ?????? ?????????
        for hotel in recommand_hotels:
            # ?????? ?????? ???????????? ?????? ??????
            if Hotel_image.objects.filter(hotel_id=hotel.hotel_id):
                hotel_imgs.append(Hotel_image.objects.get(hotel_id=hotel.hotel_id))
            # ?????? ?????? ???????????? ?????? ??????
            else:
                hotel_imgs.append("")

        # ?????? ????????? ?????????
        for vacation in recommand_vacations:
            # ?????? ????????? ???????????? ?????? ??????
            if Vacation_image.objects.filter(vacation_id=vacation.vacation_id):
                vacation_imgs.append(Vacation_image.objects.get(vacation_id=vacation.vacation_id))
            # ?????? ????????? ???????????? ?????? ??????
            else:
                vacation_imgs.append("")


        context = {
            'hotel_places' : hotel_places,
            'vacation_places' : vacation_places,
            'hotel_imgs': hotel_imgs,
            'vacation_imgs': vacation_imgs,
        }
        return render(request, 'main.html', context)

    if request.method == 'POST':
        if request.POST.get('hotel_type') == 'hotel_type' :
            SIGUN_NM = request.POST.get('SIGUN_NM')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            hotel_reserve_people = request.POST.get('hotel_reserve_people')

            request.session['SIGUN_NM'] = SIGUN_NM
            request.session['start_date'] = start_date
            request.session['end_date'] = end_date
            request.session['hotel_reserve_people'] = hotel_reserve_people

            return redirect('/hotel_search/')

        if request.POST.get('vacation_type') == 'vacation_type':
            SIGUN_NM = request.POST.get('SIGUN_NM')
            vacation_reserve_people = request.POST.get('vacation_reserve_people')
            vacation_date = request.POST.get('vacation_date')
            

            request.session['SIGUN_NM'] = SIGUN_NM
            request.session['vacation_reserve_people'] = vacation_reserve_people
            request.session['vacation_date'] = vacation_date

            return redirect('/vacation_search/')

def hotel_search(request):
    if request.method == "POST":
        SIGUN_NM = request.POST.get('SIGUN_NM')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        hotel_reserve_people = request.POST.get('hotel_reserve_people')

        request.session['SIGUN_NM'] = SIGUN_NM
        request.session['start_date'] = start_date
        request.session['end_date'] = end_date
        request.session['hotel_reserve_people'] = hotel_reserve_people

        return redirect('/hotel_search/')

    if request.method == "GET":
        now = datetime.datetime.now().strftime('%Y-%m-%d')
        nextDay = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')

        # ????????? ????????? ???????????? Query
        # table ??? ?????? ????????? ?????? ???????????????
        hotel_places = Hotel.objects.all().values('SIGUN_NM').distinct()
        
        # session ?????? ????????? ?????????, ????????????, ?????????, ???????????? ?????? 
        SIGUN_NM = request.session.get('SIGUN_NM', '?????????')
        start_date = request.session.get('start_date', now)
        end_date = request.session.get('end_date', nextDay)
        hotel_reserve_people = request.session.get('hotel_reserve_people', 1)

        # filter range??? ???????????? ?????? date??? ?????????, format ??????
        hotel_reserve_startdate = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        hotel_reserve_enddate = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # ?????? ????????? [?????? ??????] ?????? list
        # ?????? 1. room_table?????? ??????????????? ????????? ?????? ??????,
        #      2. ??????????????? ????????? ?????? ????????? ?????? ????????? ???
        #      3. ??? ??? ????????? [????????????: ?????????] ??? ??????

        # 1. ??????????????? ????????? ???
        hotel_lists = list(Hotel_reserve.objects.filter(hotel_reserve_startdate__range=[hotel_reserve_startdate, hotel_reserve_enddate]).values('room_id_id'))

        # check code
        # print("????????? ???")
        # for room in hotel_lists:
        #     print(room)
        
        # 2. ?????? ????????? ??? (+ ???????????? ??????)
        #    (?????? ????????? ??? ???????????? ????????? template?????? ??????) 
        
        # Q??? add??? ???????????? query where ?????? ??????
        # test = Hotel_room.objects.filter(room_people__gte=hotel_reserve_people).exclude(Q(room_id=1)|Q(room_id=2))
        # q.add(Q(room_id=1), q.OR)
        # q.add(Q(room_id=2), q.OR)
        # ??????
        q = Q()
        for room in hotel_lists:
            q.add(Q(room_id=room['room_id_id']), q.OR)

        pos_rooms = Hotel_room.objects.all().filter(room_people__gte=hotel_reserve_people).exclude(q)

        request.session['pos_rooms'] = list(pos_rooms.values())

        # check code
        # print("?????? ????????? ???")
        # print(pos_rooms.values())


        # 3. ?????? ????????? ??????(??? ??????:hotel_id_id??? ??????) ??? [????????????:?????????]??? ??????
        # Hotel.objects.filter(Q(SIGUN_NM = SIGUN_NM) & Q(hotel_id=1) | Q(hotel_id=2..))
        # ?????? ?????? ??????
        # ??????
        # ?????? ????????? ?????? ?????? ?????? (1) => ??????, ???????????? ?????????.
        if pos_rooms:
            q = Q()
            for room in pos_rooms:
                q.add(Q(hotel_id=room.hotel_id_id), q.OR)
            q.add(Q(SIGUN_NM = SIGUN_NM), q.AND)

            all_hotel_lists = Hotel.objects.filter(q)

            # check code
            # ?????? ????????? ?????? ?????? ?????? (2) => ??????????????? ?????????
            if not(all_hotel_lists):
                # template ?????? ??????
                all_hotel_lists = ""
            # print(all_hotel_lists)

        else:
            all_hotel_lists = ""
        
        # all_hotel_lists = Hotel.objects.filter(SIGUN_NM = SIGUN_NM)
        hotel_room = Hotel_room.objects.all()
        
        # ????????? ????????? ?????? < << 1 2 3 4 5 >> >
        write_pages = int(request.session.get('write_pages', 5))
        
        # ??? ???????????? ?????? ?????? ??????
        per_page = int(request.session.get('per_page', 5))
        
        # ?????? ?????????
        page = int(request.GET.get('page', 1))

        # ??? ???????????? 5?????? ???????????? Paginator ??????
        paginator = Paginator(all_hotel_lists, per_page)
        
        # ???????????? ?????? ??????
        page_obj = paginator.get_page(page)

        start_page = ((int)((page_obj.number - 1) / write_pages) * write_pages) + 1
        end_page = start_page + write_pages - 1

        if end_page >= paginator.num_pages:
            end_page = paginator.num_pages

        last_page=0

        for last_page in paginator.page_range:
            last_page = last_page + 1

        last_page= last_page -1
        zero = 0
        context = {
            # 'hotel': hotel,
            'hotel_places' : hotel_places,
            'lists': page_obj,  # Hotel table
            'SIGUN_NM': SIGUN_NM,
            'start_date': start_date,
            'end_date' : end_date,
            'hotel_reserve_people': hotel_reserve_people,
            'start_page': start_page,
            'end_page': end_page,
            'last_page' : last_page,
            'page_range': range(start_page, end_page + 1),
            'zero' : zero,
            'hotel_rooms' : hotel_room, # Hotel_room table
        }
        return render(request, 'hotel_search.html', context)

def vacation_search(request):
    if request.method == 'POST':
        SIGUN_NM = request.POST.get('SIGUN_NM')
        vacation_date = request.POST.get('vacation_date')
        vacation_reserve_people = request.POST.get('vacation_reserve_people')

        request.session['SIGUN_NM'] = SIGUN_NM
        request.session['vacation_date'] = vacation_date
        request.session['vacation_reserve_people'] = vacation_reserve_people

        return redirect('/vacation_search/')
    if request.method == 'GET':
        now = datetime.datetime.now().strftime('%Y-%m-%d')

        vacation_places = Vacation.objects.all().values('SIGUN_NM').distinct()
        #SIGUN_NM= OO?????? vacation ????????? ????????? 
        SIGUN_NM = request.session.get('SIGUN_NM', '?????????')
        vacation_date = request.session.get('vacation_date', now)
        vacation_reserve_people = request.session.get('vacation_reserve_people', 1)
        all_vacation_lists = Vacation.objects.filter(SIGUN_NM = SIGUN_NM)
        
        # ????????? ????????? ?????? < << 1 2 3 4 5 >> >
        write_pages = int(request.session.get('write_pages', 5))
    
        # ??? ???????????? ?????? ?????? ??????
        per_page = int(request.session.get('per_page', 5))
        
        # ?????? ?????????
        page = int(request.GET.get('page', 1))

        # ??? ???????????? 5?????? ???????????? Paginator ??????
        paginator = Paginator(all_vacation_lists, per_page)
        
        # ???????????? ?????? ??????
        page_obj = paginator.get_page(page)

        start_page = ((int)((page_obj.number - 1) / write_pages) * write_pages) + 1
        end_page = start_page + write_pages - 1

        if end_page >= paginator.num_pages:
            end_page = paginator.num_pages

        last_page=0

        for last_page in paginator.page_range:
            last_page = last_page + 1

        last_page= last_page -1
        
        context = {
            'vacation_places' : vacation_places,
            'lists': page_obj,  # vacation table
            'start_page': start_page,
            'end_page': end_page,
            'SIGUN_NM': SIGUN_NM,
            'vacation_date': vacation_date,
            'vacation_reserve_people': vacation_reserve_people,
            'last_page' : last_page,
            'page_range': range(start_page, end_page + 1),
        }
        return render(request, 'vacation_search.html', context)

def user_create(request):
    return render(request, 'user_create.html')

def hotel_reserve(request):
        id = request.session.get('user','') # session??? ????????? user??? ????????? ???????????????.
        if id == "": # session??? ????????? user ????????? ???????????? ????????????????????? redirect?????????.
            return redirect('/login/')
        # ????????? ????????? ?????? ????????? (hotel_detail ?????? ????????? ?????????) ???????????????. *?????? ????????? ?????? ??????*
        hotel_name = request.session.get('hotel_name', Hotel.objects.get(hotel_id=1).BIZPLC_NM)
        hotel_reserve_people = request.session.get('hotel_reserve_people', 2)
        hotel_reserve_startdate = request.session.get('start_date', '2022-04-01')
        hotel_reserve_enddate = request.session.get('end_date', '2022-04-02')
        start_date = datetime.datetime.strptime(hotel_reserve_startdate, '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(hotel_reserve_enddate, '%Y-%m-%d').date()
        reserve_room = request.session.get('reserve_room')

        print(hotel_name, hotel_reserve_people)

        if (hotel_reserve_people=="") or (hotel_reserve_startdate==""):
            return redirect('/main/') # session??? ??????????????? ???????????? ?????? ?????? main?????? redirect?????????.

        hotel_room_pk = request.session.get('hotel_room_pk', 1) #detail??????, ????????? ????????? pk. 
        hotel_room = Hotel_room.objects.get(pk=hotel_room_pk)       # ?????? ?????? hotel_room_id ??? ???????????????.
        night = (end_date - start_date).days
        hotel_reserve_price = hotel_room.room_price * night  # ??? ?????? ????????? ????????? ???????????? ???????????? ???????????????.
        if request.method=="GET":
            context = {
                'hotel_name': hotel_name,
                'reserve_people': hotel_reserve_people,
                'reserve_startdate':  hotel_reserve_startdate,
                'reserve_enddate': hotel_reserve_enddate,
                'reserve_room' : reserve_room,
                'night': night,
                'room_type': hotel_room.room_type,
                'hotel_price': '{0:,}'.format(hotel_reserve_price),
            }
            return render(request, 'hotel_reserve.html', context)
        elif request.method=="POST": # ???????????? ???????????? ??????

            hotel_reserve_username = request.POST["reserve_name"]
            hotel_reserve_phonenum = request.POST["phone_num"]

            id = User.objects.get(id=id) # session??? ????????? user??? ????????? ???????????????.(????????? 1??? ?????? ??????)
            room_id = hotel_room

            hotel_reserve = Hotel_reserve(
                hotel_reserve_people = hotel_reserve_people,
                hotel_reserve_username = hotel_reserve_username,
                hotel_reserve_phonenum = hotel_reserve_phonenum,
                hotel_reserve_startdate = hotel_reserve_startdate,
                hotel_reserve_enddate = hotel_reserve_enddate,
                hotel_reserve_price = hotel_reserve_price,
                id = id,
                room_id = room_id,       
            )

            hotel_reserve.save()

            return redirect(f'/hotel_confirm/?reserve={hotel_reserve.hotel_reserve_id}')

def vacation_reserve(request):   
    vacation_id = request.session.get('vacation_pk')
    vacation_reserve_people = request.session.get('vacation_reserve_people')
    vacation_reserve_date = request.session.get('vacation_date')
    if (vacation_id=="") or (vacation_reserve_people=="") or (vacation_reserve_date==""):
        return redirect('/main/') # session??? ??????????????? ???????????? ?????? ?????? main?????? redirect?????????.
    try:    
        vacation= Vacation.objects.get(vacation_id=vacation_id)
        vacation_reserve_price = vacation.vacation_price 
        vacation_reserve_people = int(vacation_reserve_people)
        place_name = vacation.TURSM_INFO_NM
        id = id=request.session.get('user','') # session??? ????????? user??? ????????? ???????????????.
        if id == "": # session??? ????????? user ????????? ???????????? ????????????????????? redirect?????????.
            return redirect('/login/')
        
        if request.method=="GET":
            
            context = {
                'place_name': place_name,
                'reserve_people': vacation_reserve_people,
                'vacation_price': vacation_reserve_price,
                'show_price': vacation_reserve_price * vacation_reserve_people,
                'vacation_reserve_date': vacation_reserve_date,
            }
            return render(request, 'vacation_reserve.html', context)

        elif request.method=="POST":
            vacation_reserve = Vacation_reserve(
                vacation_reserve_people = request.POST['peopleNum'],
                vacation_reserve_date = request.POST['end_date'],
                vacation_reserve_username = request.POST['reserve_name'],
                vacation_reserve_phonenum = request.POST['phone_num'],
                vacation_reserve_price = vacation_reserve_price * int(request.POST['peopleNum']),
                id = User.objects.get(id=id),
                vacation_id_id = vacation_id
            )
            vacation_reserve.save()
            del request.session['vacation_pk'] # vacation ?????? ??? ????????????
            del request.session['vacation_reserve_people']
            return redirect(f'/vacation_confirm/?reserve={vacation_reserve.vacation_reserve_id}')
    
    except Vacation.DoesNotExist:
        raise Http404('????????? ???????????????.')

def hotel_detail(request, pk):
    # ????????? ?????????
    # ?????? ????????? ?????????
    count = {}
    vacation_imgs = []
    
    # ?????? ????????? ????????? ????????? 
    reserve_pos = []
    now = datetime.datetime.now()
    next_date = now + datetime.timedelta(days=1)

    start_date = request.session.get('start_date')
    end_date = request.session.get('end_date')
    hotel_reserve_people = request.session.get('hotel_reserve_people')
    pos_rooms = request.session.get('pos_rooms')

    if not (start_date or end_date or hotel_reserve_people):
        request.session['start_date'] = now.strftime('%Y-%m-%d')
        request.session['end_date'] = next_date.strftime('%Y-%m-%d')
        request.session['hotel_reserve_people'] = 1
    # if not start_date or not end_date or  not hotel_reserve_people:
    #     request.session['start_date'] = now.strftime('%Y-%m-%d')
    #     request.session['end_date'] = next_date.strftime('%Y-%m-%d')
    #     request.session['hotel_reserve_people'] = 1


    if request.method == "GET":
        # search ?????? session?????? ????????? ???
        start_date = request.session.get('start_date')
        end_date = request.session.get('end_date')
        hotel_reserve_people = request.session.get('hotel_reserve_people')

        if not pos_rooms:
            # ?????? ????????? [?????? ??????] ?????? list
            # ?????? 1. room_table?????? ??????????????? ????????? ?????? ??????,
            #      2. ??????????????? ????????? ?????? ????????? ?????? ????????? ???
            #      3. ??? ??? ????????? [????????????: ?????????] ??? ??????

            # 1. ??????????????? ????????? ???
            hotel_lists = list(Hotel_reserve.objects.filter(hotel_reserve_startdate__range=[start_date, end_date]).values('room_id_id'))

            # check code
            # print("????????? ???")
            # for room in hotel_lists:
            #     print(room)
            
            # 2. ?????? ????????? ??? (+ ???????????? ??????)
            #    (?????? ????????? ??? ???????????? ????????? template?????? ??????) 
            
            # Q??? add??? ???????????? query where ?????? ??????
            # test = Hotel_room.objects.filter(room_people__gte=hotel_reserve_people).exclude(Q(room_id=1)|Q(room_id=2))
            # q.add(Q(room_id=1), q.OR)
            # q.add(Q(room_id=2), q.OR)
            # ??????
            q = Q()
            for room in hotel_lists:
                q.add(Q(room_id=room['room_id_id']), q.OR)

            pos_rooms = list(Hotel_room.objects.all().filter(room_people__gte=hotel_reserve_people).exclude(q).values())

        # check code
        for room in pos_rooms:
            # print(room)
            # key: 'room_id', 'room_type', 'room_price', 'room_people', 'hotel_id_id'
            if room['hotel_id_id'] == pk and room['room_people'] >= int(hotel_reserve_people):
                reserve_pos.append(room)

        # print(reserve_pos)

        try:
            # ?????? ??????
            hotel = Hotel.objects.get(pk=pk)
            # hotel_id ??? pk??? hotel_review ??? ?????????
            all_hotel_reviews = Hotel_review.objects.filter(hotel_id=pk).order_by('-hotel_review_id')
            # ?????? ??????,vacation_rate ??? ?????? ????????? 4??? ????????????
            recommand_vacations = Vacation.objects.filter(SIGUN_NM = hotel.SIGUN_NM).order_by('-vacation_rate')[:4]

            try:
                # hotel ?????? ?????? ????????????.
                # ????????? ??? ????????????.
                hotel_img = Hotel_image.objects.get(hotel_id=pk)
            except Hotel_image.DoesNotExist:
                hotel_img = '';

            # Pagination
            # ????????? ???????????? (1~5???) count
            for i in range(5):
                # (????????? ?????? ???) orm ??????
                count.update({i+1 : all_hotel_reviews.filter(hotel_review_rate__gt=i).filter(hotel_review_rate__lte=i+1).count()})

            # ????????? ????????? ?????? < << 1 2 3 4 5 >> >
            write_pages = int(request.session.get('write_pages', 5))
            # ??? ???????????? ?????? ?????? ??????
            per_page = int(request.session.get('per_page', 5))
            # ?????? ?????????
            page = int(request.GET.get('page', 1))

            # ??? ???????????? 5?????? ???????????? Paginator ??????
            paginator = Paginator(all_hotel_reviews, per_page)
            # ???????????? ?????? ??????
            page_obj = paginator.get_page(page)
            start_page = ((int)((page_obj.number - 1) / write_pages) * write_pages) + 1
            end_page = start_page + write_pages - 1
            if end_page >= paginator.num_pages:
                end_page = paginator.num_pages

            # ?????? ????????? ?????????
            for vacation in recommand_vacations:
                # ?????? ????????? ???????????? ?????? ??????
                if Vacation_image.objects.filter(vacation_id=vacation.vacation_id):
                    vacation_imgs.append(Vacation_image.objects.get(vacation_id=vacation.vacation_id))
                # ?????? ????????? ???????????? ?????? ??????
                else:
                    vacation_imgs.append("")

        except Hotel.DoesNotExist:
            raise Http404('???????????? ????????? ????????????')
            

        context = {
            # 'check_in' : check_in,
            # 'check_out' : check_out,
            # 'hotel_reserve_people' : hotel_reserve_people,
            'vacation_imgs': vacation_imgs,
            'hotel': hotel,
            'reviews': page_obj,
            'start_page': start_page,
            'end_page': end_page,
            'page_range': range(start_page, end_page + 1),
            'recommand_vacations' : recommand_vacations,
            'count' : count,
            'hotel_img' : hotel_img,
            'reserve_pos' : reserve_pos,
        }

        return render(request, 'hotel_detail.html', context)

    if request.method == "POST":
        hotel_pk = pk
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        hotel_reserve_people = request.POST.get('hotel_reserve_people')
        reserve_room = request.POST.get('reserve_room')
        hotel_room_pk = request.POST.get('hotel_room_pk')
        hotel_name = request.POST.get('hotel_name')

        request.session['start_date'] = start_date
        request.session['end_date'] = end_date
        request.session['hotel_pk'] = hotel_pk
        request.session['hotel_name'] = hotel_name
        request.session['hotel_reserve_people'] = hotel_reserve_people
        request.session['reserve_room'] = reserve_room
        request.session['hotel_room_pk'] = hotel_room_pk

        return redirect('/hotel_reserve/')


def vacation_detail(request, pk):
    now = datetime.datetime.now().strftime('%Y-%m-%d')
    hotel_imgs = []
    vacation_date = request.session.get('vacation_date')
    vacation_reserve_people = request.session.get('vacation_reserve_people')

    if not(vacation_date or vacation_reserve_people):
        vacation_date = now
        vacation_reserve_people = 1
        request.session['vacation_date'] = vacation_date
        request.session['vacation_reserve_people'] = vacation_reserve_people

    if request.method == "GET":
        count = {}
        try:
            vacation = Vacation.objects.get(pk=pk)
            all_vacation_reviews = Vacation_review.objects.filter(vacation_id=pk).order_by('-vacation_review_id')
            recommand_hotels = Hotel.objects.filter(SIGUN_NM = vacation.SIGUN_NM).order_by('-hotel_rate')[:4]
            
            try:
                vacation_img = Vacation_image.objects.get(vacation_id=pk)
            except Vacation_image.DoesNotExist:
                vacation_img = '';

            # ?????? ?????? ?????????
            for hotel in recommand_hotels:
                # ?????? ?????? ???????????? ?????? ??????
                if Hotel_image.objects.filter(hotel_id=hotel.hotel_id):
                    hotel_imgs.append(Hotel_image.objects.get(hotel_id=hotel.hotel_id))
                # ?????? ?????? ???????????? ?????? ??????
                else:
                    hotel_imgs.append("")

            # Pagination
            # ????????? ???????????? (1~5???) count
            for i in range(5):
                # (????????? ?????? ???) orm ??????
                count.update({i+1 : all_vacation_reviews.filter(vacation_review_rate__gt=i).filter(vacation_review_rate__lte=i+1).count()})

            # ????????? ????????? ?????? < << 1 2 3 4 5 >> >
            write_pages = int(request.session.get('write_pages', 5))
            # ??? ???????????? ?????? ?????? ??????
            per_page = int(request.session.get('per_page', 5))
            # ?????? ?????????
            page = int(request.GET.get('page', 1))

            # ??? ???????????? 5?????? ???????????? Paginator ??????
            paginator = Paginator(all_vacation_reviews, per_page)
            # ???????????? ?????? ??????
            page_obj = paginator.get_page(page)

            start_page = ((int)((page_obj.number - 1) / write_pages) * write_pages) + 1
            end_page = start_page + write_pages - 1
            

            if end_page >= paginator.num_pages:
                end_page = paginator.num_pages

        except Hotel.DoesNotExist:
            raise Http404('???????????? ????????? ????????????')
            

        context = {
            'vacation_date' : vacation_date,
            'vacation_reserve_people' : vacation_reserve_people,
            'hotel_imgs': hotel_imgs,
            'vacation': vacation,
            'reviews': page_obj,
            'start_page': start_page,
            'end_page': end_page,
            'page_range': range(start_page, end_page + 1),
            'recommand_hotels' : recommand_hotels,
            'count' : count,
            'vacation_img' : vacation_img,
        }

        return render(request, 'vacation_detail.html', context)

    if request.method == "POST":
        vacation_pk = pk
        vacation_reserve_people = request.POST.get('vacation_reserve_people')
        vacation_reserve_date = request.POST.get('end_date') # ?????? end_date??? ??????????????? ??????????????? ???????????????. (?????? ????????? ????????????????????? datepicker ?????? ??????)

        request.session['vacation_reserve_date'] = vacation_reserve_date
        request.session['vacation_reserve_people'] = vacation_reserve_people
        request.session['vacation_pk'] = vacation_pk

        return redirect('/vacation_reserve/')

def login(request):
    context = {
    }

    if request.method == 'POST':
        user_id = request.POST.get('id')
        user_pw = request.POST.get('pw')
        try:
            user = User.objects.get(user_id = user_id)
        except User.DoesNotExist:
            return redirect('/loginFail/')
        context = {
            'user' : user,
        }
        if user.user_password == user_pw:
            request.session['user'] = user.id
            request.session['user_type'] = user.user_type
            # request.session['user_email'] = user.user_email

            # context['logged'] = True
            # context['id'] = user.id
            # context['user_id'] = user_id
            # context['user_type'] = user.user_type
            # context['user'] = user
            # print(context['user_type'],  context['user_id'], context['logged'], context['id'], context['user'].user_password)
            return render(request, 'loginOk.html', context)
        elif user.user_password != user_pw:
            return redirect('/loginFail/')

    return render(request, 'login.html', context)

def logout(request):
    request.session.flush()
    return render(request, 'logout.html')

def loginFail(request):
    return render(request, 'loginFail.html')

def hotel_confirm(request):
    reserve_id = request.GET['reserve']
    reserve_info = Hotel_reserve.objects.get(hotel_reserve_id=reserve_id)
    # room_type = Hotel_room.objects.get(room_id=reserve_info.room_id        

    context = {
        'reserve_info': reserve_info, 
        'hotel': Hotel.objects.get(hotel_id = reserve_info.room_id.hotel_id.hotel_id).BIZPLC_NM,
        'price': '{0:,}'.format(reserve_info.hotel_reserve_price),
        'night': (reserve_info.hotel_reserve_enddate - reserve_info.hotel_reserve_startdate).days
        }   
    return render(request, 'hotel_confirm.html', context)

def vacation_confirm(request):
    reserve_id = request.GET['reserve']
    reserve_info = Vacation_reserve.objects.get(vacation_reserve_id=reserve_id)
    place = Vacation.objects.get(vacation_id = reserve_info.vacation_id_id).TURSM_INFO_NM
    context = {
        'reserve_info': reserve_info, 
        'place': place,
        'price': '{0:,}'.format(reserve_info.vacation_reserve_price),
        }   
    return render(request, 'vacation_confirm.html', context)

def user_divide(request):
    if request.method == "GET":
        return render(request, 'user_divide.html')
    elif request.method == "POST":
        join_type = request.POST.get('join_type') # ?????? ???????????? ?????? ?????? ?????? ????????? ????????? ?????? ????????? 'user_type' ?????? ?????? ???????????? ??????????????????.
        request.session['join_type'] = join_type
        return redirect('/user_create')

def user_create(request):
    user_type = request.session['join_type'] # ?????????????????? ????????? ?????? ?????? ??????. admin ?????? basic

    if request.method == 'POST':
        user_id = request.POST.get('id')
        user_password = request.POST.get('pw')
        if user_type == 'admin':    # ????????? ????????? user_type ??? 1 ?????????.
            user_type = 1
        elif user_type == 'basic':  # ??????????????? user_type??? 2 ?????????.
            user_type = 2

        user_email = request.POST.get('email')
        user_phonenum = request.POST.get('phonenum')

        user = User(
            user_id = user_id,
            user_password = user_password,
            user_type = user_type,
            user_email = user_email,
            user_phonenum = user_phonenum
        )

        user.save()
        del request.session['join_type'] # ???????????? ??????. ?????? ??????
        return redirect('/login/')

    return render(request, 'user_create.html')

def user_info(request):
    pk = request.session['user']
    
    if request.method=="POST":
        # ?????????, ??????????????? ????????? ????????? ??????
        user = User.objects.get(pk=pk)
        user_phonenum = request.POST.get('user_phonNum')
        user_email = request.POST.get('user_email')

        user.user_phonenum = user_phonenum
        user.user_email = user_email
        user.save()

        context = {
            'user': user,
        }

        return render(request, 'user_info.html', context)
    if request.method=="GET":
        user = User.objects.get(pk=pk)
        context = {
            'user': user
        }
        return render(request, 'user_info.html', context)

def pw_change(request):
    pk = request.session['user']

    user = User.objects.get(pk=pk)
    context = {
        'user':user
    }
    if request.method == 'POST':
        now_password = request.POST.get('current_pw')
        if now_password != user.user_password:
            return redirect('/pw_changeFail2/')
        user_password = request.POST.get('confirm_pw')

        user.user_password = user_password
        user.save()
        request.session.flush()
        return redirect('/pw_changeOk/')

    return render(request, 'pw_change.html', context)

def pw_changeOk(request):
    return render(request, 'pw_changeOk.html')

def history_hotel(request):
    pk = request.session['user']

    user = User.objects.get(pk=pk)
    hotel_reserve = Hotel_reserve.objects.filter(id=pk).order_by('-hotel_reserve_enddate')
    # hotel_reserves = []

    try:
        hotel_image = Hotel_image.objects.get(pk=hotel_reserve[0].room_id.hotel_id)

    except Hotel_image.DoesNotExist:
        hotel_image = ''
    
    except IndexError:
        hotel_image = ''
    

    # for i in range(hotel_reserve.count()):
    #     hotel_reserves.append(hotel_reserve[i])

    # ??? ???????????? ?????? ?????? ??????
    per_page = 5
    # ?????? ?????????
    page = int(request.GET.get('page',1))
    # ?????????????????? ??????
    paginator = Paginator(hotel_reserve, per_page)
    # ????????? ?????? 
    page_obj = paginator.get_page(page)
    # ????????? ????????? ??????. 
    write_pages = int(request.session.get('write_pages', 5))
    # ???????????????
    start_page =((int)((page_obj.number -1 ) / write_pages) * write_pages) + 1
    end_page = start_page + write_pages -1
    if end_page >= paginator.num_pages:
        end_page = paginator.num_pages

    # hotel_reserves = []
    # hotel_image = Hotel_image.objects.get(pk=hotel_reserve[0].room_id.hotel_id)

    # for i in range(hotel_reserve.count()):
    #     hotel_reserves.append(hotel_reserve[i])
    
    context = {
        'user': user,
        'hotel_reserves' : page_obj,
        'start_page' : start_page,
        'end_page' : end_page,
        'page_range' : range(start_page, end_page + 1),
        'hotel_image' : hotel_image,
        'today': datetime.datetime.now().date(),        
    }

    if request.method == 'POST':
        review = request.POST.get('review')
        rate = request.POST.get('rate')
        hotel_id = request.POST.get('hotel_id')
        hotel = Hotel.objects.get(pk=hotel_id)
        now = datetime.datetime.now().strftime('%Y-%m-%d')

        hotel_review = Hotel_review(
            hotel_review_content = review,
            hotel_review_rate = rate,
            hotel_review_date = now,

            id = user,
            hotel_id = hotel
        )

        hotel_review.save()

        all_cnt = Hotel_review.objects.filter(hotel_id_id = hotel_id).count()
        hotel.hotel_rate = round((hotel.hotel_rate * (all_cnt-1) + int(rate)) / all_cnt, 2)    # ????????? ?????????????????? ??????????????????.
        hotel.save()
        return redirect(f'/hotel_detail/{hotel_id}')

    return render(request, 'history_hotel.html', context)

def history_vacation(request):
    pk = request.session['user']

    user = User.objects.get(pk=pk)
    vacation_reserve = Vacation_reserve.objects.filter(id=pk).order_by('-vacation_reserve_date')

    # ??? ???????????? ?????? ?????? ??????
    per_page = 5
    # ?????? ?????????
    page = int(request.GET.get('page',1))
    # ?????????????????? ??????
    paginator = Paginator(vacation_reserve, per_page)
    # ????????? ?????? 
    page_obj = paginator.get_page(page)
    # ????????? ????????? ??????. 
    write_pages = int(request.session.get('write_pages', 5))
    # ???????????????
    start_page =((int)((page_obj.number - 1) / write_pages) * write_pages) + 1
    end_page = start_page + write_pages -1
    if end_page >= paginator.num_pages:
        end_page = paginator.num_pages
    
    context = {
        'user': user,
        'vacation_reserves': page_obj,
        'start_page': start_page,
        'end_page': end_page,
        'page_range': range(start_page, end_page+1),
        'today': datetime.datetime.now().date()
    }
    if request.method == 'POST':
        review = request.POST.get('review')
        rate = request.POST.get('rate')
        vacation_id = request.POST.get('vacation_id')
        vacation = Vacation.objects.get(pk=vacation_id)
        now = datetime.datetime.now().strftime('%Y-%m-%d')

        vacation_review = Vacation_review(
            vacation_review_content = review,
            vacation_review_rate = rate,
            vacation_review_date = now,
            id = user,
            vacation_id = vacation
        )

        vacation_review.save()

        all_cnt = Vacation_review.objects.filter(vacation_id_id = vacation_id).count()
        vacation.vacation_rate = round((vacation.vacation_rate * (all_cnt-1) + int(rate)) / all_cnt, 2)    # ????????? ?????????????????? ??????????????????.
        vacation.save()
        return redirect(f'/vacation_detail/{vacation_id}')
    return render(request, 'history_vacation.html', context)

def admin_info(request):
    pk = request.session['user']
    
    if request.method=="POST":
        # ?????????, ??????????????? ????????? ????????? ??????
        user = User.objects.get(pk=pk)
        user_phonenum = request.POST.get('user_phonNum')
        user_email = request.POST.get('user_email')

        user.user_phonenum = user_phonenum
        user.user_email = user_email
        user.save()

        context = {
            'user': user,
        }

        return render(request, 'admin_info.html', context)
    if request.method=="GET":
        user = User.objects.get(pk=pk)
        context = {
            'user': user
        }
        return render(request, 'admin_info.html', context)

def admin_pw_change(request):
    pk = request.session['user']
    
    user = User.objects.get(pk=pk)
    context = {
        'user':user
    }
    if request.method == "POST":
        now_password = request.POST.get('current_pw')
        if now_password != user.user_password:
            return redirect('/pw_changeFail/')
        user_password = request.POST.get('confirm_pw')

        user.user_password = user_password
        user.save()
        request.session.flush()
        return redirect('/pw_changeOk/')

    return render(request, 'admin_pw_change.html', context)

def pw_changeFail(request):
    return render(request, 'pw_changeFail.html')

def pw_changeFail2(request):
    return render(request, 'pw_changeFail2.html')

def admin_hotel(request):
    pk = request.session['user']

    user = User.objects.get(pk=pk)
    hotel = Hotel.objects.filter(hotel_admin_id = user.id)
    # hotels = []
    # for i in range(hotel.count()):
    #     hotels.append(hotel[i])
    # per_page = 5
    page = int(request.GET.get('page',1))
    paginator = Paginator(hotel, 5)
    page_obj = paginator.get_page(page)
    write_pages = int(request.session.get('write_pages', 5))
    # ???????????????
    start_page = ((int)((page_obj.number-1) / write_pages) * write_pages) + 1
    end_page = start_page + write_pages -1
    if end_page >= paginator.num_pages:
        end_page = paginator.num_pages

    context = {
        'user' : user,
        'hotels' : page_obj,
        'start_page': start_page,
        'end_page': end_page,
        'page_range': range(start_page, end_page+1),
    }

    return render(request, 'admin_hotel.html', context)
    '''
    pk=request.session['user']
    if request.method=="POST":
        hotels=Hotel.objects.get(pk=pk) 
        

   
    
    # ????????? ???????????? (1~5???) count
    # count={}
    # for i in range(5):
    # #     # (????????? ?????? ???) orm ??????
    # #     # ?????? https://dev-yakuza.posstree.com/ko/django/orm/
    #     count.update({i+1 : hotels.filter(hotel_rate__gt=i).filter(hotel_rate__lte=i+1).count()})
    # # ????????? ????????? ?????? < << 1 2 3 4 5 >> >
    # write_pages = int(request.session.get('write_pages', 5))

    # # ??? ???????????? ?????? ?????? ??????
    # per_page = int(request.session.get('per_page', 5))

    # # ?????? ?????????
    # page = int(request.GET.get('page', 1))

    # # ??? ???????????? 5?????? ???????????? Paginator ??????
    # paginator = Paginator(hotels, per_page)
    
    # # ???????????? ?????? ??????
    # page_obj = paginator.get_page(page)

    # start_page = ((int)((page_obj.number - 1) / write_pages) * write_pages) + 1
    # end_page = start_page + write_pages - 1

    # if end_page >= paginator.num_pages:
    #     end_page = paginator.num_pages

    # last_page=0

    # for last_page in paginator.page_range:
    #     last_page = last_page + 1

    # last_page= last_page -1
    

    
   
    '''
    # five=5
    # i =1

    # context={
    #      'five' : five,
    #      'i' : i 
    #     # 'hotels' : hotels
    #     # 'lists' : page_obj,
    #     # 'start_page': start_page,
    #     # 'end_page': end_page,
    #     # 'last_page' : last_page,
    #     # 'page_range': range(start_page, end_page + 1),
    #     # 'count' : count,

    # }
    

    # return render(request, 'admin_hotel.html', context)

def admin_vacation(request):
    pk = request.session['user']

    user = User.objects.get(pk=pk)
    vacation = Vacation.objects.filter(vacation_admin_id = user.id)

    per_page = 5
    page = int(request.GET.get('page',1))
    paginator = Paginator(vacation, per_page)
    page_obj = paginator.get_page(page)
    write_pages = 5
    # ???????????????
    start_page =((int)((page_obj.number-1) / write_pages) * write_pages) + 1
    end_page = start_page + write_pages -1
    if end_page >= paginator.num_pages:
        end_page = paginator.num_pages

    context = {
        'user' : user,
        'vacations' : page_obj,
        'start_page': start_page,
        'end_page': end_page,
        'page_range': range(start_page, end_page+1),
    }
    return render(request, 'admin_vacation.html', context)

def admin_manage(request):
    pk = request.session['user']
    user = User.objects.get(pk=pk)
    my_hotels = Hotel.objects.filter(hotel_admin_id_id=pk)
    my_vacations = Vacation.objects.filter(vacation_admin_id_id=pk)
    context = {
        'hotel': my_hotels,
        'vacation': my_vacations,
        'user' : user,
    }
    
    if request.method == "POST":

        choice = request.POST.get('choice') # ????????????, ??????????????? ???????????? ??????
        reserve_name = request.POST.get('reserve_name')
        reserve_num = request.POST.get('reserve_num')
        reserve_date = request.POST.get('reserve_date')
        reserve_date = re.sub('[^0-9]', '', reserve_date)
        if choice == 'hotel':
            selected_place = request.POST.get('choice_hotel')
            if selected_place == "default":
                return redirect('/admin_manage/')
            hotel_id = Hotel.objects.get(BIZPLC_NM=selected_place).hotel_id
            rooms_2 = Hotel_room.objects.filter(hotel_id=hotel_id)
            reserveses = []
            for r in range(rooms_2.count()):
                reserve = Hotel_reserve.objects.filter(room_id=rooms_2[r].room_id)
                for i in range(reserve.count()):
                    reserveses.append(reserve[i])
                    
                    # reserveses = reserveses[0: reserve.count()]
            if reserve_name != '':
                reserveses = list(filter(lambda x: x.hotel_reserve_username == reserve_name, reserveses))
            if reserve_num != '':
                reserveses = list(filter(lambda x: str(x.hotel_reserve_id) == str(reserve_num), reserveses))
            if reserve_date != '':
                reserveses = list(filter(lambda x: re.sub('[^0-9]', '', str(x.hotel_reserve_startdate)) == reserve_date, reserveses))
            if len(reserveses) == 0 :
                context['message'] = '??????????????? ????????????.' 
            context['place_type'] = 'hotel'
            context['reserves'] = reserveses
            context['reserve_count'] = len(reserveses)
            context['selected'] = selected_place
            return render(request, 'admin_manage.html', context)

            # reserves = Hotel_reserve.objects.filter(q).values().order_by('-hotel_reserve_startdate')
            # print(reserves[0].room_id_id)
            # hotel_room = Hotel_room.objects.filter(hotel_id_id = hotel_id)
            # rooms = []
            # for r in hotel_room:
            #     rooms.append(hotel_room.room_id)
            # print(rooms)
            # reserves = Hotel_reserve.objects.filter(room_id_id.hotel_id = hotel_id)
            # room_id = Hotel_room.objects.filter(hotel_id_id=hotel_id)
            # ????????? hotel ??? ????????? ?????? room?????? room_id ??? ??????. => room_id[r].room_id
            # reserve ??? room_id_id??? ??? ?????? ??? ????????? ?????? -> ?????????
            # for r in room_id:
            #     temp_list = Hotel_reserve.objects.filter(room_id=room_id[r].room_id) 
            
        elif choice == 'vacation':
            selected_place = request.POST.get('choice_vacation')
            if selected_place == "default":
                return redirect('/admin_manage/')
            vacation_id = Vacation.objects.get(TURSM_INFO_NM=selected_place).vacation_id
            reserves = Vacation_reserve.objects.filter(vacation_id_id=vacation_id).order_by('-vacation_reserve_date')
            if reserve_name != '':
                reserves = reserves.filter(vacation_reserve_username=reserve_name)
            if reserve_num != '':
                reserves = reserves.filter(vacation_reserve_id=reserve_num)
            if reserve_date != '':
                reserves = reserves.filter(vacation_reserve_date=reserve_date)
            if reserves.count() == 0 :
                context['message'] = '??????????????? ????????????.' 
            context['place_type'] = 'vacation'
            context['reserve_count'] = reserves.count()
            context['reserves'] = reserves
            context['selected'] = selected_place
            return render(request, 'admin_manage.html', context)

    if request.method == "GET":
        return render(request, 'admin_manage.html', context)




def hotel_register(request):
    pk = request.session['user']
    user = User.objects.get(pk=pk)

    if request.method == 'POST':
        BIZPLC_NM = request.POST.get('hotel_name')
        SIGUN_NM = request.POST.get('hotel_area')
        BSN_STATE_NM = 1
        REFINE_ROADNM_ADDR = request.POST.get('hotel_addr', '')
        REFINE_WGS84_LAT = request.POST.get('lat')
        REFINE_WGS84_LOGT = request.POST.get('lng')
        hotel_rate = 0.0
        hotel_comment = request.POST.get('context')
        hotel_admin_id = user
        if hotel_comment == '':
            hotel_comment = '????????? ????????????.'

        hotel = Hotel(
            BIZPLC_NM = BIZPLC_NM,
            SIGUN_NM = SIGUN_NM,
            BSN_STATE_NM = BSN_STATE_NM,
            REFINE_ROADNM_ADDR = REFINE_ROADNM_ADDR,
            REFINE_WGS84_LAT = REFINE_WGS84_LAT,
            REFINE_WGS84_LOGT = REFINE_WGS84_LOGT,
            hotel_rate = hotel_rate,
            hotel_comment = hotel_comment,
            hotel_admin_id = hotel_admin_id,
        )

        hotel.save()

        hotel_id = Hotel.objects.get(pk = hotel.hotel_id)
        hotel_image_title = request.POST['fileTitle']
        hotel_image_file_path = request.FILES["uploadedFile"]
        document = Hotel_image(
            hotel_id = hotel_id,
            hotel_image_title = hotel_image_title,
            hotel_image_file_path = hotel_image_file_path,
            hotel_image_originname = "",
        )
        document.save()

        room_type = request.POST.getlist('room_type[]')
        room_price = request.POST.getlist('room_price[]')
        room_people = request.POST.getlist('room_people[]')
        all_room = len(room_type)
        if room_type[-1] == "":
            all_room -= 1

        for i in range(all_room):
            hotel_room = Hotel_room(
                room_type = room_type[i],
                room_price = room_price[i],
                room_people = room_people[i],

                hotel_id = hotel_id
            )
            
            hotel_room.save()

        return redirect('/admin_hotel/')

    context = {
        'user' : user,
    }
    return render(request, 'hotel_register.html', context)

def hotel_delete(request):
    pk = request.session['user']
    user = User.objects.get(pk=pk)
    context = {
        'user' : user,
    }

    return render(request, 'hotel_delete.html', context)

def hotel_delete2(request):
    pk = request.session['user']
    user = User.objects.get(pk=pk)
    temp = request.POST.get('hotel_reserve_id')
    request.session['rk2'] = temp
    print(temp)
    context = {
        'user' : user,
    }

    return render(request, 'hotel_delete2.html', context)  


def hotel_deleteOk(request):
    pk = request.session['user']
    user = User.objects.get(pk=pk)
    hotel_id = request.session.get('hk')
    hotel = Hotel.objects.get(pk=hotel_id)
    hotel.delete()
    context = {
        'user' : user,
    }

    return render(request, 'hotel_deleteOk.html', context)

def hotel_deleteOk2(request):
    pk = request.session['user']
    user = User.objects.get(pk=pk)
    hotel_reserve_id = request.session.get('rk2')
    hotel_reserve = Hotel_reserve.objects.get(pk=hotel_reserve_id)
    hotel_reserve.delete()
    context = {
        'user' : user,
    }

    return render(request, 'hotel_deleteOk2.html', context)

def vacation_register(request):
    pk = request.session['user']
    user = User.objects.get(pk=pk)

    if request.method == 'POST':
        SIGUN_NM = request.POST.get('SIGUN_NM')
        TURSM_INFO_NM = request.POST.get('vacation_name')
        SM_RE_ADDR =  request.POST.get('vacation_adress')
        TELNO =  request.POST.get('phoneNum')
        REFINE_WGS84_LAT = request.POST.get('lat')
        REFINE_WGS84_LOGT = request.POST.get('lng')
        vacation_comment = request.POST.get('context')
        vacation_price = request.POST.get('vacation_price')
        vacation_rate = 0.0
        vacation_admin_id = user
        if vacation_comment == '':
            vacation_comment = '????????? ????????????.'

        vacation = Vacation(
            SIGUN_NM = SIGUN_NM,
            TURSM_INFO_NM = TURSM_INFO_NM,
            SM_RE_ADDR = SM_RE_ADDR,
            TELNO = TELNO,
            REFINE_WGS84_LAT = REFINE_WGS84_LAT,
            REFINE_WGS84_LOGT = REFINE_WGS84_LOGT,
            vacation_comment = vacation_comment,
            vacation_price = vacation_price,
            vacation_rate = vacation_rate,
            vacation_admin_id = vacation_admin_id,
        )

        vacation.save()

        vacation_id = Vacation.objects.get(pk = vacation.vacation_id)
        vacation_image_title = request.POST['fileTitle']
        vacation_image_file_path = request.FILES["uploadedFile"]
        document = Vacation_image(
            vacation_id = vacation_id,
            vacation_image_title = vacation_image_title,
            vacation_image_file_path = vacation_image_file_path,
            vacation_image_originname = "",
        )
        document.save()

        return redirect('/admin_vacation/')

    context = {
        'user' : user,
    }
    return render(request, 'vacation_register.html', context)

def vacation_delete(request):
    pk = request.session['user']
    user = User.objects.get(pk=pk)
    context = {
        'user' : user,
    }

    return render(request, 'vacation_delete.html', context)

def vacation_delete2(request):
    pk = request.session['user']
    user = User.objects.get(pk=pk)
    temp = request.POST.get('vacation_reserve_id')
    request.session['rk'] = temp
    print(temp)
    context = {
        'user' : user,
    }

    return render(request, 'vacation_delete2.html', context)  

def vacation_deleteOk(request):
    pk = request.session['user']
    user = User.objects.get(pk=pk)
    vacation_id = request.session.get('vk')
    vacation = Vacation.objects.get(pk=vacation_id)
    vacation.delete()
    context = {
        'user' : user,
    }

    return render(request, 'vacation_deleteOk.html', context)

def vacation_deleteOk2(request):
    pk = request.session['user']
    user = User.objects.get(pk=pk)
    vacation_reserve_id = request.session.get('rk')
    vacation_reserve = Vacation_reserve.objects.get(pk=vacation_reserve_id)
    vacation_reserve.delete()
    context = {
        'user' : user,
    }

    return render(request, 'vacation_deleteOk2.html', context)

def admin_hotel_detail(request, hk):
    pk = request.session['user']
    request.session['hk'] = hk
    user = User.objects.get(pk=pk)
    hotel = Hotel.objects.get(pk = hk)
    hotel_review = Hotel_review.objects.filter(hotel_id = hk) 
    hotel_room = Hotel_room.objects.filter(hotel_id = hk)
    all_review = hotel_review.count()

    context = {
        'user' : user,
        'hotel' : hotel,
        'hotel_reviews' : hotel_review,
        'hotel_rooms' : hotel_room,
        'all_review' : all_review,
    }
    return render(request, 'admin_hotel_detail.html', context)

def admin_vacation_detail(request, hk):
    pk = request.session['user']
    request.session['vk'] = hk
    user = User.objects.get(pk=pk)
    vacation = Vacation.objects.get(pk = hk)
    vacation_review = Vacation_review.objects.filter(vacation_id = hk)
    all_review = vacation_review.count()

    context = {
        'user' : user,
        'vacation' : vacation,
        'vacation_reviews' : vacation_review,
        'all_review' : all_review,
    }

    return render(request, 'admin_vacation_detail.html',context )

def hotel_update(request):
    pk = request.session['user']
    user = User.objects.get(pk=pk)
    hotel_id = request.session.get('hk')
    hotel = Hotel.objects.get(pk=hotel_id)
    hotel_room = Hotel_room.objects.filter(hotel_id = hotel.hotel_id)

    if request.method == 'POST':
        BIZPLC_NM = request.POST.get('hotel_name')
        SIGUN_NM = request.POST.get('hotel_area')
        BSN_STATE_NM = 1
        REFINE_ROADNM_ADDR = request.POST.get('hotel_addr', '')
        REFINE_WGS84_LAT = request.POST.get('lat')
        REFINE_WGS84_LOGT = request.POST.get('lng')
        hotel_comment = request.POST.get('context')
        hotel_admin_id = user
        if hotel_comment == '':
            hotel_comment = '????????? ????????????.'
        
        hotel.BIZPLC_NM = BIZPLC_NM
        hotel.SIGUN_NM = SIGUN_NM
        hotel.BSN_STATE_NM = BSN_STATE_NM
        hotel.REFINE_ROADNM_ADDR = REFINE_ROADNM_ADDR
        hotel.REFINE_WGS84_LAT = REFINE_WGS84_LAT
        hotel.REFINE_WGS84_LOGT = REFINE_WGS84_LOGT
        hotel.hotel_comment = hotel_comment
        hotel.hotel_admin_id = hotel_admin_id
        
        hotel.save()

        hotel_id = Hotel.objects.get(pk = hotel.hotel_id)
        hotel_image_title = request.POST['fileTitle']
        hotel_image_file_path = request.FILES["uploadedFile"]
        document = Hotel_image(
            hotel_id = hotel_id,
            hotel_image_title = hotel_image_title,
            hotel_image_file_path = hotel_image_file_path,
            hotel_image_originname = "",
        )
        document.save()

        room_type = request.POST.getlist('room_type[]')
        room_price = request.POST.getlist('room_price[]')
        room_people = request.POST.getlist('room_people[]')
        all_room = len(room_type)

        # for i in range(all_room):

        #     print(hotel_room[i])
        #     print(hotel_room[i].room_type, room_type[i])
        #     hotel_room[i].room_type = room_type[i]
        #     print(hotel_room[i].room_type, room_type[i])
        #     # hotel_room[i].room_prcie = room_price[i]
        #     # hotel_room[i].room_people = room_people[i]
        #     hotel_room[i].save()

        #     # hotel_room.update(room_type=room_type[i])
        # for hotel_room in range(all_room):
        #     hotel_room.room_type = room_type

        i = 0
        for room in hotel_room:
            room.room_type = room_type[i]
            room.room_price = room_price[i]
            room.room_people = room_people[i]
            i += 1
        Hotel_room.objects.bulk_update(hotel_room, ['room_type'])
        Hotel_room.objects.bulk_update(hotel_room, ['room_price'])
        Hotel_room.objects.bulk_update(hotel_room, ['room_people'])
        
        for i in range(i, all_room):
            hotel_room = Hotel_room(
                room_type = room_type[i],
                room_price = room_price[i],
                room_people = room_people[i],

                hotel_id = hotel_id                
            )

            hotel_room.save()
        
        return redirect('/admin_hotel/')
    context = {
        'user' : user,
        'hotel' : hotel,
        'hotel_rooms' : hotel_room,
    }
    return render(request, 'hotel_update.html', context)

def vacation_update(request):
    pk = request.session['user']
    user = User.objects.get(pk=pk)
    vacation_id = request.session.get('vk')
    vacation = Vacation.objects.get(pk=vacation_id)

    if request.method == 'POST':
        SIGUN_NM = request.POST.get('SIGUN_NM')
        TURSM_INFO_NM = request.POST.get('vacation_name')
        SM_RE_ADDR =  request.POST.get('vacation_adress')
        TELNO =  request.POST.get('phoneNum')
        REFINE_WGS84_LAT = request.POST.get('lat')
        REFINE_WGS84_LOGT = request.POST.get('lng')
        vacation_comment = request.POST.get('context')
        vacation_price = request.POST.get('vacation_price')
        if vacation_comment == '':
            vacation_comment = '????????? ????????????.'
        
        vacation.SIGUN_NM = SIGUN_NM
        vacation.TURSM_INFO_NM = TURSM_INFO_NM
        vacation.SM_RE_ADDR = SM_RE_ADDR
        vacation.TELNO = TELNO
        vacation.REFINE_WGS84_LAT = REFINE_WGS84_LAT
        vacation.REFINE_WGS84_LOGT = REFINE_WGS84_LOGT
        vacation.vacation_comment = vacation_comment
        vacation.vacation_price = vacation_price
    
        vacation.save()

        vacation_id = Vacation.objects.get(pk = vacation.vacation_id)
        vacation_image_title = request.POST['fileTitle']
        vacation_image_file_path = request.FILES["uploadedFile"]
        document = Vacation_image(
            vacation_id = vacation_id,
            vacation_image_title = vacation_image_title,
            vacation_image_file_path = vacation_image_file_path,
            vacation_image_originname = "",
        )
        document.save()

        return redirect('/admin_vacation/')
        
    context = {
        'user' : user,
        'vacation' : vacation,
    }
    
    return render(request, 'vacation_update.html', context)

def sample(request):  # vacation_review ????????? ?????????????????????.

    vacation_review_content = 'sample??????????????????.'
    vacation_review_rate = random.randint(1, 5)
    
    id = User.objects.get(pk=1)
    # id = User.objects.get(pk=pk)  pk ?????? ???????????? ??????
    vacation_id = Vacation.objects.get(pk=1)
    # vacation_id = Vacation.objects.get(pk=pk)
    vacation_review = Vacation_review(
        vacation_review_content = vacation_review_content,
        vacation_review_rate = vacation_review_rate,
        id = id,
        vacation_id = vacation_id
    )
    vacation_review.save()


    all_cnt = Vacation_review.objects.filter(vacation_id_id = 1).count()    # ???????????? vacation_id ??? ?????????????????????. filter(vacation_id_id = pk)
    vacation_id.vacation_rate = round((vacation_id.vacation_rate * (all_cnt-1) + vacation_review_rate) / all_cnt, 2)    # ????????? ?????????????????? ??????????????????.
    vacation_id.save()

    return render(request, 'sample.html')

def sample2(request):  # vacation_reserve ????????? ?????????????????????.

    vacation_reserve_people = 3
    vacation_reserve_date = '2022-12-31'
    vacation_reserve_username = '?????????'
    vacation_reserve_phonenum = '010-1234-5678'

    id = User.objects.get(pk=3)
    # id = User.objects.get(pk=pk)
    vacation_id = Vacation.objects.get(pk=485)

    vacation_reserve_price = vacation_id.vacation_price * vacation_reserve_people  # ???????????? + ?????? ???

    vacation_reserve = Vacation_reserve(
        vacation_reserve_people = vacation_reserve_people,
        vacation_reserve_date = vacation_reserve_date,
        vacation_reserve_username = vacation_reserve_username,
        vacation_reserve_phonenum = vacation_reserve_phonenum,
        vacation_reserve_price = vacation_reserve_price,
        id = id,
        vacation_id = vacation_id
    )

    vacation_reserve.save()

    return render(request, 'sample2.html')

def sample3(request):   # hotel_room ???????????????.

    room_type = "?????????"
    room_price = 67586
    room_people = 2

    hotel_id = Hotel.objects.get(pk=90)  # ????????? ???????????? pk?????? ????????? ?????? ?????????????????????.

    hotel_room = Hotel_room(
        room_type = room_type,
        room_price = room_price,
        room_people = room_people,

        hotel_id = hotel_id
    )

    hotel_room.save()

    return render(request, 'sample3.html')

def sample4(request):   # hotel_reserve ???????????????.
    
    hotel_reserve_people = 2
    hotel_reserve_username = '?????????'
    hotel_reserve_phonenum = '010-1234-5678'
    hotel_reserve_startdate = '2022-03-02'
    hotel_reserve_enddate = '2022-03-03'

    hotel_room = Hotel_room.objects.get(pk=100)       # ?????? ?????? hotel_room_id ??? ???????????????.
    hotel_reserve_price = hotel_room.room_price     # ??? ?????? ????????? ????????? ???????????? ???????????? ???????????????.

    id = User.objects.get(pk=14)
    room_id = hotel_room

    hotel_reserve = Hotel_reserve(
        hotel_reserve_people = hotel_reserve_people,
        hotel_reserve_username = hotel_reserve_username,
        hotel_reserve_phonenum = hotel_reserve_phonenum,
        hotel_reserve_startdate = hotel_reserve_startdate,
        hotel_reserve_enddate = hotel_reserve_enddate,
        hotel_reserve_price = hotel_reserve_price,
        
        id = id,
        room_id = room_id        
    )

    hotel_reserve.save()

    return render(request, 'sample4.html')

def sample5(request):       # hotel_review ???????????????.

    hotel_review_content = 'sample ??????????????????.'
    hotel_review_rate = 5
    hotel_review_date = datetime.datetime.now().strftime('%Y-%m-%d')    # ??????????????? YYYY-MM-DD????????? ???????????????.
    id = User.objects.get(pk=3)             # ????????? primary key ??? ????????? ???????????????. 

    # peongtaek_hotels = [1,2,3,4,5,6,7,25,88,89,90,91,113,192,193,195,200,212,216,256,310,337,363]


    for i in range(3):
        hotel_id = Hotel.objects.get(pk = 42)    # ????????? primary key ??? ????????? ???????????? ?????????. pk=pk
        hotel_review = Hotel_review(
            hotel_review_content = hotel_review_content,
            hotel_review_rate = hotel_review_rate,
            hotel_review_date = hotel_review_date,
            id = id,
            hotel_id = hotel_id
        )

        hotel_review.save()

        all_cnt = Hotel_review.objects.filter(hotel_id_id = 5).count()    # ???????????? vacation_id ??? ?????????????????????. filter(vacation_id_id = pk)
        hotel_id.hotel_rate = round((hotel_id.hotel_rate * (all_cnt-1) + hotel_review_rate) / all_cnt, 2)    # ????????? ?????????????????? ??????????????????.
        hotel_id.save()

    return render(request, 'sample5.html')

def sample6(request):   # hotel_image ???????????????.  vacation_image ??? hotel => vacation ?????? ???????????? ???????????????.
    # if request.method == "GET":
    #     request.session()
    if request.method == "POST":
        hotel_id = Hotel.objects.get(pk=1)      # ?????? ????????? ???????????? ???????????? ?????????. ex) pk = pk
        hotel_image_title = request.POST['fileTitle']
        hotel_image_file_path = request.FILES["uploadedFile"]

        document = Hotel_image(
            hotel_id = hotel_id,
            hotel_image_title = hotel_image_title,
            hotel_image_file_path = hotel_image_file_path,
            hotel_image_originname = hotel_image_file_path.name,
        )
        document.save()
    
    documents = Hotel_image.objects.all().order_by("-pk")

    return render(request, 'sample6.html', {"sample6s" : documents})

def sample7(request):   # vacation_image ???????????????.  vacation_image ??? vacation => vacation ?????? ???????????? ???????????????.
    # if request.method == "GET":
    #     request.session()
    if request.method == "POST":
        vacation_id = Vacation.objects.get(pk=1)      # ?????? ????????? ???????????? ???????????? ?????????. ex) pk = pk
        vacation_image_title = request.POST['fileTitle']
        vacation_image_file_path = request.FILES["uploadedFile"]

        document = Vacation_image(
            vacation_id = vacation_id,
            vacation_image_title = vacation_image_title,
            vacation_image_file_path = vacation_image_file_path,
            vacation_image_originname = vacation_image_file_path.name,
        )
        document.save()
    
    documents = Vacation_image.objects.all().order_by("-pk")

    return render(request, 'sample7.html', {"sample7s" : documents})

# def api(request):

#     KEY = unquote("db11faf6254746fbb71311dedf6cdb3d")
#     url = "https://openapi.gg.go.kr/StayingTourismHotel"
#     Type = "xml"
#     pSize = "500"
#     pindex = "1"  # ?????? ???????????? ??????????????????.

#     queryParmas = '?' + urlencode({ 
#         quote_plus('KEY') : KEY,
#         quote_plus('Type') : Type,
#         quote_plus('pindex') : pindex,
#         quote_plus('pSize') : pSize
#     })

#     res = requests.get(url + queryParmas).text.encode('utf-8')
#     xmlobj = bs4.BeautifulSoup(res, 'lxml-xml')
#     rows = xmlobj.findAll('row')

#     rowList = []
#     nameList = []
#     columnList = []

#     rowsLen = len(rows)
#     for i in range(0, rowsLen):
#         columns = rows[i].find_all()
        
#         columnsLen = len(columns)
#         for j in range(0, columnsLen):

#             if i == 0:
#                 nameList.append(columns[j].name)
  
#             eachColumn = columns[j].text
#             columnList.append(eachColumn)
#         rowList.append(columnList)
#         columnList = []    

#     result = pd.DataFrame(rowList, columns=nameList)
#     print(result)

#     for i in range(int(pSize)):
#         columns = rows[i].find_all()
#         BIZPLC_NM = columns[2].text             # ????????????
#         SIGUN_NM = columns[1].text              # ?????????
#         BSN_STATE_NM = True                     # ???????????????
#         REFINE_ROADNM_ADDR = columns[15].text   # ????????????????????????
#         REFINE_WGS84_LAT = columns[18].text     # WGS??????
#         if columns[18].text == "":
#             REFINE_WGS84_LAT = 0.0
#         REFINE_WGS84_LOGT = columns[17].text    # WGS??????
#         if columns[17].text == "":
#             REFINE_WGS84_LOGT = 0.0
#         hotel_rate = 0.0
#         hotel_comment = "????????? ????????????."

#         hotel_admin_id = User.objects.get(pk=1)

#         hotel = Hotel(
#             BIZPLC_NM = BIZPLC_NM, 
#             SIGUN_NM = SIGUN_NM, 
#             BSN_STATE_NM = BSN_STATE_NM, 
#             REFINE_ROADNM_ADDR = REFINE_ROADNM_ADDR, 
#             REFINE_WGS84_LAT = REFINE_WGS84_LAT, 
#             REFINE_WGS84_LOGT = REFINE_WGS84_LOGT,
#             hotel_comment = hotel_comment,
#             hotel_rate = hotel_rate,
#             hotel_admin_id = hotel_admin_id,
#             )
        
#         hotel.save()

#     # user_id = 'user1'
#     # user_password = '1234'
#     # user_type = '1'
#     # user_email = 'test@email.com'
#     # user_phonenum = '010-1234-5678'

#     # user = User(user_id = user_id, user_password = user_password, user_type = user_type, user_email = user_email, user_phonenum = user_phonenum)
#     # user.save()   #????????? ?????? ?????? 

#     return render(request, 'api.html')

# def api2(request):

#     KEY = unquote("db11faf6254746fbb71311dedf6cdb3d")
#     url = "https://openapi.gg.go.kr/CTST"
#     Type = "xml"
#     pSize = "481"
#     pindex = "1"  # ?????? ???????????? ??????????????????.

#     queryParmas = '?' + urlencode({ 
#         quote_plus('KEY') : KEY,
#         quote_plus('Type') : Type,
#         quote_plus('pindex') : pindex,
#         quote_plus('pSize') : pSize
#     })
    
#     res = requests.get(url + queryParmas).text.encode('utf-8')
#     xmlobj = bs4.BeautifulSoup(res, 'lxml-xml')
#     rows = xmlobj.findAll('row')

#     for i in range(int(pSize)):
#         columns = rows[i].find_all()
#         SIGUN_NM = columns[0].text
#         TURSM_INFO_NM = columns[1].text
#         SM_RE_ADDR = columns[2].text
#         TELNO = columns[3].text
#         REFINE_WGS84_LAT = columns[5].text
#         if columns[5].text == "":
#             REFINE_WGS84_LAT = 0.0
#         REFINE_WGS84_LOGT = columns[6].text
#         if columns[6].text == "":
#             REFINE_WGS84_LOGT = 0.0
#         vacation_comment = "????????? ????????????."
#         vacation_price = 100000
#         vacation_rate = 0.0

#         vacation_admin_id = User.objects.get(pk=1)

#         vacation = Vacation(
#             SIGUN_NM = SIGUN_NM,
#             TURSM_INFO_NM = TURSM_INFO_NM,
#             SM_RE_ADDR = SM_RE_ADDR,
#             TELNO = TELNO,
#             REFINE_WGS84_LAT = REFINE_WGS84_LAT,
#             REFINE_WGS84_LOGT = REFINE_WGS84_LOGT,
#             vacation_comment = vacation_comment,
#             vacation_price = vacation_price,
#             vacation_rate = vacation_rate,
#             vacation_admin_id = vacation_admin_id
#         )

#         vacation.save()

#     return render(request, 'api2.html')

def option_change(request, pk):
    # ??????, ???????????? ????????? ??????????????? ???
    reserve_pos = []
    if request.method == "POST":
        start_date = request.POST.get('start_date', '?????????')
        end_date = request.POST.get('end_date', '????????????')
        hotel_reserve_people = request.POST.get('hotel_reserve_people', 1)

        request.session['start_date'] = start_date
        request.session['end_date'] = end_date
        request.session['hotel_reserve_people'] = hotel_reserve_people

        # ?????? ????????? [?????? ??????] ?????? list
        # ?????? 1. room_table?????? ??????????????? ????????? ?????? ??????,
        #      2. ??????????????? ????????? ?????? ????????? ?????? ????????? ???
        #      3. ??? ??? ????????? [????????????: ?????????] ??? ??????

        # 1. ??????????????? ????????? ???
        hotel_lists = list(Hotel_reserve.objects.filter(hotel_reserve_startdate__range=[start_date, end_date]).values('room_id_id'))

        # check code
        # print("????????? ???")
        # for room in hotel_lists:
        #     print(room)
        
        # 2. ?????? ????????? ??? (+ ???????????? ??????)
        #    (?????? ????????? ??? ???????????? ????????? template?????? ??????) 
        
        # Q??? add??? ???????????? query where ?????? ??????
        # test = Hotel_room.objects.filter(room_people__gte=hotel_reserve_people).exclude(Q(room_id=1)|Q(room_id=2))
        # q.add(Q(room_id=1), q.OR)
        # q.add(Q(room_id=2), q.OR)
        # ??????
        q = Q()
        for room in hotel_lists:
            q.add(Q(room_id=room['room_id_id']), q.OR)

        pos_rooms = list(Hotel_room.objects.all().filter(room_people__gte=hotel_reserve_people).exclude(q).values())

        if pos_rooms:
        # check code
            for room in pos_rooms:
                # print(room)
                # key: 'room_id', 'room_type', 'room_price', 'room_people', 'hotel_id_id'
                if room['hotel_id_id'] == pk and room['room_people'] >= int(hotel_reserve_people):
                    reserve_pos.append(room)

            # print(reserve_pos)

        context = {
            'start_date' : start_date,
            'end_date' : end_date,
            'hotel_reserve_people' : hotel_reserve_people,
            'reserve_pos': reserve_pos,
            'pos_rooms': pos_rooms,
        }

        # print(json.dumps(context))
        return HttpResponse(json.dumps(context), content_type="application/json")
        # context??? json ????????????
    else:
        raise Http404