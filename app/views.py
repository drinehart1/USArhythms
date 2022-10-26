from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect #, get_object _or_404
from django.template import loader
from django.http import HttpResponse, JsonResponse, QueryDict
from django import template
from django.template.loader import render_to_string
from django.urls import reverse
from django.views import View
from django.contrib import messages
from app.models import PARAM_stored, PARAM_sections, PARAM_methods, PARAM_stored_values
from app.utils import set_pagination
from django.db import connection
import datetime


@login_required(login_url="/login/")
def index(request):
    context = {'segment': 'index'}
    html_template = loader.get_template('index.html')

    param_researcher_id = request.user.id  # LOGGED IN USER

    params = PARAM_stored.objects.all()
    total_param = 0
    user_param = 0
    for param in params:
        if param.FK_userid == param_researcher_id:
            user_param += 1
        total_param += 1
    context['param_count'] = total_param
    context['user_param_count'] = user_param

    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
def pages(request):
    context = {}
    # All resource paths end in .html.
    # Pick out the html file name from the url. And load that template.
    try:

        load_template = request.path.split('/')[-1]
        context['segment'] = load_template

        html_template = loader.get_template(load_template)
        return HttpResponse(html_template.render(context, request))

    except template.TemplateDoesNotExist:

        html_template = loader.get_template('page-404.html')
        return HttpResponse(html_template.render(context, request))

    except:

        html_template = loader.get_template('page-500.html')
        return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def ListParam(request):
    '''
        LIST/SEARCH PARAMETER SETS (TABULAR)
    '''
    context = {}
    param_researcher_id = request.user.id  # LOGGED IN USER

    sql = '''
            SELECT  a.id, c.name AS PERF_CTR, b.name AS PERF_LAB, d.email AS EMAIL, CONCAT(d.last_name, ", ", d.first_name) AS NAME, e.description AS EXP_TYPE, objectid_uuid AS UUID, a.FK_session_id AS SESSION_ID
            FROM PARAM_stored a
            INNER JOIN performance_lab b ON a.FK_performance_lab_id = b.id 
            INNER JOIN performance_center c ON b.FK_performance_center_id = c.id
            INNER JOIN auth_user d ON a.FK_userid = d.id
            INNER JOIN PARAM_exp_type e ON a.FK_exp_type = e.id
            '''
    context['output'] = PARAM_stored.objects.raw(sql)

    return render(request, 'list_param.html', context)


@login_required(login_url="/login/")
def StoreParam(request):
    '''
        STORE VALUES FROM SUBMITTED FORM (POPULATES PARAM_stored AND PARAM_stored_values TABLES)
    '''
    context = {}
    param_sql = []

    if request.method == 'POST':  # STORE FORM VARIABLES
        for formvar in request.POST:
            param_researcher_id = request.user.id  # LOGGED IN USER
            if formvar != 'csrfmiddlewaretoken':
                form_raw_field_name = formvar.split("-")
                PARAM_value = request.POST[formvar]

                try:
                    PARAM_optionid = form_raw_field_name[1]
                    # CORE PARAM FIELDS:
                    if PARAM_optionid == '1':
                        param_session_id = PARAM_value
                    elif PARAM_optionid == '2':
                        if request.user.is_superuser: #ONLY ADMIN CAN DELEGATE PARAMETER SETS
                            param_researcher_id = PARAM_value
                        else:
                            param_researcher_id = request.user.id
                    elif PARAM_optionid == '3':
                        param_performance_lab_id = PARAM_value
                    elif PARAM_optionid == '4':
                        param_publication_name = PARAM_value
                    elif PARAM_optionid == '5':
                        param_doi = PARAM_value
                    elif PARAM_optionid == '6':  # identifier and description as of 7-SEP-2022
                        param_desc = PARAM_value
                        param_identifier = PARAM_value
                    else:
                        if PARAM_value.isalnum() and PARAM_optionid != 'content': #has value but not a method
                            param_sql.append(f'{base_param_id, PARAM_optionid, PARAM_value}')
                except:
                    pass

                if formvar == 'method-content-4': #exptype PULLS FROM 'DATA ACQUISITION' METHOD
                    param_exp_type = request.POST['method-content-4']
                if formvar == 'edit_paramid':
                    base_param_id = request.POST['edit_paramid']

        if base_param_id != 'None':  # UPDATE EXISTING PARAMETER SET
            #PARAM_stored : table holding primary indexed parametersets
            #PARAM_stored_values : table holding all parameterset values

            record = PARAM_stored.objects.get(id=base_param_id)
            record.description = param_desc
            record.identifier = param_identifier
            record.doi_pub = param_doi
            record.FK_exp_type = param_exp_type
            record.FK_session_id = param_session_id
            record.publication_name = param_publication_name
            record.save(update_fields=['description', 'identifier', 'doi_pub', 'FK_exp_type', 'FK_session_id', 'publication_name'])

            PARAM_stored_values.objects.filter(FK_parameterid=base_param_id).delete() # equivalent to: f'DELETE FROM PARAM_stored_values WHERE FK_parameterid = {base_param_id}'

            param_sql_insert = 'INSERT INTO param_stored_values (FK_parameterid, FK_optionid, finalvalue) VALUES '
            param_sql_insert += ",".join(param_sql)
            cursor = connection.cursor()
            response = cursor.execute(param_sql_insert)

            print(param_sql_insert, response)


        else:
            #NEW PARAMETERSET; NO EXISTING

            a = PARAM_stored(description=param_desc, identifier=param_identifier, doi_pub=param_doi,
                             FK_userid=param_researcher_id, FK_exp_type=param_exp_type, FK_session_id=param_session_id, FK_performance_lab_id=param_performance_lab_id)
            a.save()

            PARAM_stored_values


    # ALL UPDATES, REDIRECT USER TO DASHBOARD
    return redirect('/')


@login_required(login_url="/login/")
def CreateParam(request):
    '''
        USED FOR CREATE PARAMETER SETS (DISPLAY AVAILABLE OPTIONS)
        AND
        STORE VALUES FROM SUBMITTED FORM (IF POST)
    '''
    context = {}

    param_researcher_id = request.user.id  # LOGGED IN USER
    requested_param_id = request.GET.get('id')  # VIEW PARAM ID (PASSED FROM SEARCH FORM)

    if requested_param_id:
        # VIEW/STORED VALUES (OVERRIDE) OF REQUESTED PARAMETER SET
        # NOTE: DJANGO LIMITATION REQUIRES RESULTS TO INCLUDE PRIMARY KEY OF BASE TABLE (HENCE '*' IN SELECT STATEMENT)
        # ADDED DEFAULT=KLEINFELD LAB IF FK_performance_lab IS NULL
        param_sql = f'''
                SELECT *, a.sectionid AS SECTIONID, b.ordering AS ORDERING, b.displayName AS OPTION_DISPLAY, optionid AS OPTIONID, b.toolTip AS TOOLTIP, b.type AS FIELDTYPE, b.method AS DEFAULT_METHOD, b.displayHTML AS DISPLAY_HTML, c.methodname AS METHOD_NAME,
                    CASE
                    WHEN OPTIONID = '1'
                        THEN (SELECT FK_session_id FROM PARAM_stored WHERE id={requested_param_id})
                    WHEN OPTIONID = '3'
                        THEN (SELECT IFNULL(FK_performance_lab, "1") FROM auth_user WHERE id={param_researcher_id})
                    WHEN OPTIONID = '4'
                     THEN (SELECT publication_name FROM PARAM_stored WHERE id={requested_param_id})
                    WHEN OPTIONID = '5'
                        THEN (SELECT doi_pub FROM PARAM_stored WHERE id={requested_param_id})
                    WHEN OPTIONID = '6'
                        THEN (SELECT DESCRIPTION FROM PARAM_stored WHERE id={requested_param_id})
                    WHEN d.finalvalue IS NOT NULL
                        THEN d.finalvalue
                    ELSE
                        b.default_value
                    END AS DEFAULT_VALUE
                FROM PARAM_sections a
                LEFT JOIN PARAM_options b ON b.FK_sectionid = a.sectionid
                LEFT JOIN PARAM_methods c ON c.methodid = b.method
                LEFT JOIN PARAM_stored_values d ON d.FK_optionid=b.optionid
                LEFT JOIN PARAM_stored e ON e.id=d.FK_parameterid
                ORDER BY SECTIONID ASC, ORDERING ASC
                    '''
    else:
        # RESEARCH INTAKE FORM [ALL OPTIONS]; NO EXISTING PARAMETER ID
        param_sql = '''
            SELECT *, a.sectionid AS SECTIONID, b.displayName AS OPTION_DISPLAY, c.methodname AS METHOD_NAME, c.methodid AS METHOD_ID
            FROM PARAM_sections a
            LEFT JOIN PARAM_options b ON b.FK_sectionid = a.sectionid
            LEFT JOIN PARAM_methods c ON c.methodid = b.method
            ORDER BY sectionid ASC, ordering ASC;
            '''

    transactions = PARAM_sections.objects.raw(param_sql)
    methods = PARAM_methods.objects.all()
    context['edit_paramid'] = requested_param_id
    context['transactions'] = transactions
    context['methods'] = methods
    return render(request, 'accounts/create_param.html', context)


class IntakeView(View):
    context = {'segment': 'intake'}

    def get(self, request, pk=None, action=None):
        context, template = self.list(request)

        if not context:
            html_template = loader.get_template('page-500.html')
            return HttpResponse(html_template.render(self.context, request))

        return render(request, template, context)

    def post(self, request, pk=None, action=None):
        #ALL VARIABLES CAPTURED FROM QUERY STRING UNDER 'request.POST' (dict)
        param_objectid_uuid = '' #GENERATED OFF-LINE; ONLY USED ON UPDATE
        param_researcher_id = request.user.id

        for formvar in request.POST:
            if formvar != 'csrfmiddlewaretoken':
                form_raw_field_name = formvar.split("-")
                PARAM_value = request.POST[formvar]

                PARAM_optionid = form_raw_field_name[1]

                #CORE PARAM FIELDS:
                if PARAM_optionid == '1':
                    param_session_id = PARAM_value
                elif PARAM_optionid == '2':
                    # if request.user.is_superuser: #ONLY ADMIN CAN DELEGATE PARAMETER SETS
                    #     param_researcher_id = PARAM_value
                    # else:
                    #    param_researcher_id = request.user.id
                    pass
                elif PARAM_optionid == '3':
                    param_performance_lab_id = PARAM_value
                elif PARAM_optionid == '5':
                    param_doi = PARAM_value
                elif PARAM_optionid == '6': #identifier and description as of 7-SEP-2022
                    param_desc = PARAM_value
                    param_identifier = PARAM_value
                else:
                    print(PARAM_optionid, PARAM_value)

        param_exp_type = 1 #1 = Widefield imaging

        # CREATE PARAM_stored (UNIQUE PARAMETER SET) & CAPTURE id
        try:
            param_performance_lab_id
            a = PARAM_stored(description=param_desc, identifier=param_identifier, doi_pub=param_doi, FK_userid=param_researcher_id, FK_performance_lab_id=param_performance_lab_id, FK_exp_type=param_exp_type, FK_session_id=param_session_id)
        except NameError:
            a = PARAM_stored(description=param_desc, identifier=param_identifier, doi_pub=param_doi, FK_userid=param_researcher_id, FK_exp_type=param_exp_type, FK_session_id=param_session_id)
        a.save()

        # sql = f'''
        #             INSERT INTO PARAM_stored (description, identifier, doi_pub, objectid_uuid, FK_userid, FK_performance_lab_id, FK_exp_type, FK_session_id)
        #             VALUES ({param_desc}, {param_identifier}, {param_doi}, {param_objectid_uuid}, {param_researcher_id}, {param_performance_lab_id}, {param_exp_type}, {param_session_id})
        #             '''
        # print(sql)

        # INSERT/UPDATE PARAMETER SET VALUES BASED ON PARAMETER id
        #PARAM_stored.objects.raw(sql)
        param_id = PARAM_stored.objects.latest('id')
        print(f'NEW PARAM: {param_id}')


        return redirect('intake')


    def put(self, request, pk, action=None):
        is_done, message = self.update_instance(request, pk, True)
        edit_row = self.get_row_item(pk)
        return JsonResponse({'valid': 'success' if is_done else 'warning', 'message': message, 'edit_row': edit_row})

    """ Get pages """

    def list(self, request):

        # 19-SEP-2022
        # load entire parameter set based on id in QueryParam
        # if user is admin or user owns param -> display save/update button

        param_researcher_id = request.user.id #LOGGED IN USER
        requested_param_id = request.GET.get('id') #VIEW PARAM ID (PASSED FROM SEARCH FORM)

        #VIEW/STORED VALUES (OVERRIDE) OF REQUESTED PARAMETER SET
        #NOTE: DJANGO LIMITATION REQUIRES RESULTS TO INCLUDE PRIMARY KEY OF BASE TABLE (HENCE '*' IN SELECT STATEMENT)
        load_param_sql = f'''
            SELECT *, a.sectionid AS SECTIONID, b.ordering AS ORDERING, b.displayName AS OPTION_DISPLAY, optionid AS OPTIONID, b.toolTip AS TOOLTIP, b.type AS FIELDTYPE, b.method AS DEFAULT_METHOD, b.displayHTML AS DISPLAY_HTML, c.methodname AS METHOD_NAME,
                CASE
                WHEN OPTIONID = '1'
                    THEN (SELECT FK_session_id FROM PARAM_stored WHERE id={requested_param_id})
                WHEN OPTIONID = '3'
                    THEN (SELECT FK_performance_lab FROM auth_user WHERE id={param_researcher_id})
                WHEN OPTIONID = '5'
                    THEN (SELECT doi_pub FROM PARAM_stored WHERE id={requested_param_id})
                WHEN OPTIONID = '6'
                    THEN (SELECT DESCRIPTION FROM PARAM_stored WHERE id={requested_param_id})
                WHEN d.finalvalue IS NOT NULL
			        THEN d.finalvalue
                ELSE
                    b.default_value
                END AS DEFAULT_VALUE
            FROM PARAM_sections a
            LEFT JOIN PARAM_options b ON b.FK_sectionid = a.sectionid
            LEFT JOIN PARAM_methods c ON c.methodid = b.method
            LEFT JOIN PARAM_stored_values d ON d.FK_optionid=b.optionid
            LEFT JOIN PARAM_stored e ON e.id=d.FK_parameterid
            ORDER BY SECTIONID ASC, ORDERING ASC
                '''

        #RESEARCH INTAKE FORM [ALL OPTIONS]
        new_param_sql = '''
        SELECT *, a.sectionid AS SECTIONID, b.displayName AS OPTION_DISPLAY, c.methodname AS METHOD_NAME
            FROM PARAM_sections a
            LEFT JOIN PARAM_options b ON b.FK_sectionid = a.sectionid
            LEFT JOIN PARAM_methods c ON c.methodid = b.method
             
            ORDER BY sectionid ASC, ordering ASC;
        '''

        if requested_param_id:
            transactions = PARAM_sections.objects.raw(load_param_sql)
        else:
            transactions = PARAM_sections.objects.raw(new_param_sql)

        self.context['transactions'] = transactions

        if not self.context['transactions']:
            return False, self.context['info']

        return self.context, 'app/transactions/intake.html'

    def edit(self, request, pk):
        transaction = self.get_object(pk)

        self.context['transaction'] = transaction
        self.context['form'] = TransactionForm(instance=transaction)

        return self.context, 'app/transactions/edit.html'

    """ Get Ajax pages """

    def edit_row(self, pk):
        transaction = self.get_object(pk)
        form = TransactionForm(instance=transaction)
        context = {'instance': transaction, 'form': form}
        return render_to_string('app/transactions/edit_row.html', context)

    """ Common methods """

    def get_object(self, pk):
        transaction = get_object_or_404(Transaction, id=pk)
        return transaction

    def get_row_item(self, pk):
        transaction = self.get_object(pk)
        edit_row = render_to_string('app/transactions/edit_row.html', {'instance': transaction})
        return edit_row

    def update_instance(self, request, pk, is_urlencode=False):
        transaction = self.get_object(pk)
        form_data = QueryDict(request.body) if is_urlencode else request.POST
        form = TransactionForm(form_data, instance=transaction)
        if form.is_valid():
            form.save()
            if not is_urlencode:
                messages.success(request, 'Transaction saved successfully')

            return True, 'Transaction saved successfully'

        if not is_urlencode:
            messages.warning(request, 'Error Occurred. Please try again.')
        return False, 'Error Occurred. Please try again.'


class TransactionView(View):
    context = {'segment': 'transactions'}

    def get(self, request, pk=None, action=None):


        if pk and action == 'edit':
            context, template = self.edit(request, pk)
        else:
            context, template = self.list(request)

        if not context:
            html_template = loader.get_template('page-500.html')
            return HttpResponse(html_template.render(self.context, request))

        return render(request, template, context)

    def post(self, request, pk=None, action=None):
        self.update_instance(request, pk)
        return redirect('transactions')

    def put(self, request, pk, action=None):
        is_done, message = self.update_instance(request, pk, True)
        edit_row = self.get_row_item(pk)
        return JsonResponse({'valid': 'success' if is_done else 'warning', 'message': message, 'edit_row': edit_row})

    def delete(self, request, pk, action=None):
        transaction = self.get_object(pk)
        transaction.delete()

        redirect_url = None
        if action == 'single':
            messages.success(request, 'Item deleted successfully')
            redirect_url = reverse('transactions')

        response = {'valid': 'success', 'message': 'Item deleted successfully', 'redirect_url': redirect_url}
        return JsonResponse(response)

    """ Get pages """

    def list(self, request):
        #REVISED FOR HIGH-LEVEL LISTING OF META-DATA
        filter_params = None

        search = request.GET.get('search')
        if search:
            filter_params = None
            for key in search.split():
                if key.strip():
                    if not filter_params:
                        filter_params = Q(bill_for__icontains=key.strip())
                    else:
                        filter_params |= Q(bill_for__icontains=key.strip())


        #transactions = Transaction.objects.filter(filter_params) if filter_params else Transaction.objects.all()
        sql = '''
        SELECT  a.id, c.name AS PERF_CTR, b.name AS PERF_LAB, d.email AS EMAIL, CONCAT(d.last_name, ", ", d.first_name) AS NAME, e.description AS EXP_TYPE, objectid_uuid AS UUID, a.FK_session_id AS SESSION_ID
        FROM PARAM_stored a
        INNER JOIN performance_lab b ON a.FK_performance_lab_id = b.id 
        INNER JOIN performance_center c ON b.FK_performance_center_id = c.id
        INNER JOIN auth_user d ON a.FK_userid = d.id
        INNER JOIN PARAM_exp_type e ON a.FK_exp_type = e.id
        '''
        #print(sql)
        transactions = PARAM_stored.objects.raw(sql)

        self.context['transactions'], self.context['info'] = set_pagination(request, transactions)
        if not self.context['transactions']:
            return False, self.context['info']

        return self.context, 'app/transactions/list.html'

    def edit(self, request, pk):
        transaction = self.get_object(pk)

        self.context['transaction'] = transaction
        self.context['form'] = TransactionForm(instance=transaction)

        return self.context, 'app/transactions/edit.html'

    """ Get Ajax pages """

    def edit_row(self, pk):
        transaction = self.get_object(pk)
        form = TransactionForm(instance=transaction)
        context = {'instance': transaction, 'form': form}
        return render_to_string('app/transactions/edit_row.html', context)

    """ Common methods """

    def get_object(self, pk):
        transaction = get_object_or_404(Transaction, id=pk)
        return transaction

    def get_row_item(self, pk):
        transaction = self.get_object(pk)
        edit_row = render_to_string('app/transactions/edit_row.html', {'instance': transaction})
        return edit_row

    def update_instance(self, request, pk, is_urlencode=False):
        transaction = self.get_object(pk)
        form_data = QueryDict(request.body) if is_urlencode else request.POST
        form = TransactionForm(form_data, instance=transaction)
        if form.is_valid():
            form.save()
            if not is_urlencode:
                messages.success(request, 'Transaction saved successfully')

            return True, 'Transaction saved successfully'

        if not is_urlencode:
            messages.warning(request, 'Error Occurred. Please try again.')
        return False, 'Error Occurred. Please try again.'
