#--------------------------------------------------IMPORT LIBRARIES
import requests, json, urllib
import urllib.request
import yaml
import csv

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

#-------------------------------------------------------METHODS
class LookerApi(object):
    def __init__(self, token, secret, host):
            
            self.token = token
            self.secret = secret
            self.host = host

            self.session = requests.Session()
            self.session.verify = False
            self.session.trust_env = False

            self.auth()

    def auth(self):
        url = '{}{}'.format(self.host,'login')
        params = {'client_id':self.token,
                  'client_secret':self.secret}
        r = self.session.post(url,params=params)
        access_token = r.json().get('access_token')
        # print(access_token)
        head = {'Authorization': 'token {}'.format(access_token)}
        self.head = head
        self.session.headers.update(head)
        
    #GET /dashboards/search #searches a dashboard , API call returns an array of dashboard objects
    def get_dashboard(self,dashID,fields =''):
        url = '{}dashboards/{}'.format(self.host,dashID)
        params = {"fields":fields}
        response = self.session.get(url,params=params) #call getting the fields
        
        if response.status_code == requests.codes.ok:
            response_list = response.json()
            
        filters = []
#         print(response_list)
        for filter_ in response_list['dashboard_filters']:
            if ' ' in filter_['name']:
                filter_.update({'default_value_edited':filter_['name'].replace(' ','%20')})
                filters.append({'dash_name':response_list['title'],'name':filter_['name'], 
                            'default_value_edited': filter_['default_value_edited'],
                            'default_value':filter_['default_value'],'type':filter_['field']['type']})
            else:
                filters.append({'dash_name':response_list['title'],'name':filter_['name'], 
                            'default_value':filter_['default_value'],'type':filter_['field']['type']})
            
        return filters
        
    #POST /render_tasks/lookml_dashboards/{dashboard_id}/{result_format} 
    def dashboard_to_pdf(self,dash_id, output_format,body, width, height,fields = ''):
        url = '{}{}/{}/{}/{}?{}&{}'.format(self.host,'render_tasks','dashboards',dash_id,output_format,
                                              'width='+str(width),'height='+str(height))
#         print(url)
        response = self.session.post(url,json = body) #call getting the fields
#         print(response.request.body)
        
        if response.status_code == requests.codes.ok:
            response = response.json()
        
        return response
    #GET /render_tasks/{render_task_id}
    def render(self, render_id,fields=''):
        url = '{}{}/{}'.format(self.host,'render_tasks',render_id)
#         print(url)
        r = self.session.get(url)
        if r.status_code == requests.codes.ok:
            return r.json()  
        
    #GET /render_tasks/{render_task_id}/results
    def render_results(self, render_id,fields=''):
        url = '{}{}/{}/{}'.format(self.host,'render_tasks',render_id,'results')
#         print(url)
        r = self.session.get(url)
        if r.status_code == requests.codes.ok:
            return r.content
        
    def write_dash_to_pdf(self,file_name,height,width,output,dash_id,body={}):
        Height = height
        Width = width
        Output_format  = output
        Dash_id = dash_id
        Body = body
        
        response = self.dashboard_to_pdf(Dash_id, Output_format,Body, Width, Height)
        
        while True:
            report = self.render(response['id'])  

            if report['status'] == 'success':
                break
        
        results = self.render_results(response['id'])

        # print(resultss)

        file_ = open(str(file_name)+'.'+Output_format,'wb+') 
        # write it to PDF
        file_.write(results)
        
    def create_url_query_str(self):
        #CAPTURING WHICH FILTERS TO USE FROM CONSOLE AND CHANGING IT TO URL QUERY LANGUAGE
        filter_dict={}
        filters = input("Specify 'dashboard_filters' in this format, Filter Name:Desired Value. Seperate with commas, NO SPACES in between: ")

        filter_list = filters.split(',')
        for filter_pair in filter_list:
            item = filter_pair.split(':')
        #     print(item)
            #MEANT TO ACCOUNT FOR ALL POSSIBLE CASES OF SPACES AND REPLACE THEM WITH %20
            if ' ' in item[0] and ' ' in item[1]:
                filter_dict.setdefault(item[0].replace(' ','%20'), item[1].replace(' ','%20'))
            elif ' ' in item[0]:
                filter_dict.setdefault(item[0].replace(' ','%20'), item[1])
            elif ' ' in item[1]:
                filter_dict.setdefault(item[0], item[1].replace(' ','%20'))
            else:
                filter_dict.setdefault(item[0], item[1])
#         print(filter_dict)

        #THIS IS MEANT TO CREATE THE URL QUERY STRING WE WILL USE IN THE write_dash_to_pdf CALL
        urlstr = ""
        i = 0

        for item in filter_dict:
            i+=1
            urlstr+=item+'='
            if i == len(filter_dict)-1:
                urlstr+=filter_dict[item]+'&'
            else:
                urlstr+=filter_dict[item]
        
        return urlstr

#---------------------------------------------------------------------------EXECUTABLE CODE        
#Opening the conig file and instantiating API
f = open('config.yml')
params = yaml.safe_load(f)
f.close()

my_host = params['hosts']['localhost']['host']
my_secret = params['hosts']['localhost']['secret']
my_token = params['hosts']['localhost']['token']
looker = LookerApi(my_token,my_secret,my_host)

filters = looker.get_dashboard('92')

#ASKING FOR FILE NAME
file_name = input('What would you like to name this file?: ')

#ASKING WHICH DASHBOARD STYLE
style = input("Specify 'dashboard_style': ")

#DISPLAYING THE NAME OF THE DASHBOARD AND INFORMATION ABOUT AVAILABLE FILTERS
print('\nFor Dashboard "'+filters[0]['dash_name']+'" these are the available filters:')
for filter_ in filters:
    print('Filter Name: '+filter_['name'])
    print('Default Value: '+ filter_['default_value'])
    print('Datatype Filter Accepts: '+ filter_['type']+'\n')

urlstr = looker.create_url_query_str()
# print(urlstr)
body = {
    "dashboard_filters": urlstr,
    "dashboard_style": style
}

looker.write_dash_to_pdf(file_name,900,900,'pdf',92,body)
filters_ = looker.get_dashboard('92')
print('done')