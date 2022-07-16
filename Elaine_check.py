from selenium import webdriver
import math
from selenium.webdriver.chrome.options import Options as ChromeOptions
import os
from selenium.webdriver.common.by import By
import json
import queue
import re
import pdb
import ast
from selenium.webdriver.support import expected_conditions as EC
# from hanging_threads import start_monitoring
import time
from selenium.webdriver.support.wait import WebDriverWait
from browsermobproxy import Server
import pandas as pd
from multiprocessing import Pool
import multiprocessing
import subprocess

class Login():
    def check_if_login(self):
        # try:
        user = os.environ.get('USERNAME')
        option = webdriver.ChromeOptions()
        option.add_experimental_option('excludeSwitches', ['enable-logging'])
        option.add_argument('--user-data-dir=' + r'C:\Users\%s\AppData\Local\Google\Chrome\User Data' % user)
        self.driver = webdriver.Chrome(executable_path=os.path.join(os.getcwd(), "chromedriver.exe"), options=option)
        self.driver.get('https://midway-auth.amazon.com/login')
        # time.sleep(2)
        # pdb.set_trace()
        #@todo 这里不登陆的情况也会继续程序，提醒跑这个工具的人先登陆一下midway再跑
        #让程序先访问https://prod.elaine.exporteligibility.amazon.dev然后输入midway的界面显示下面这行的文字可以作为判断是否需要登陆的依据
        #XPATH //*[@id="auth-container"]/p 里是to continue to prod.elaine.exporteligibility.amazon.dev可以作为
        # try:
        #     raw_login_data = self.driver.find_element(By.XPATH, '//*[@id="input-params"]').get_attribute('data-session-status')
        #     login_data = json.loads(self.driver.find_element(By.XPATH, '//*[@id="input-params"]').get_attribute('data-session-status'))
        # except:
        find_login_data_flag= False
        while not find_login_data_flag:
            try:
                raw_login_data = self.driver.find_element(By.XPATH, '//*[@id="input-params"]').get_attribute(
                    'data-session-status')
                login_data = json.loads(raw_login_data)
                find_login_data_flag = True
            except:
                self.driver.refresh()
            # // *[ @ id = "main-message"] / h1 / span
        if login_data['authenticated'] == False:
            # pdb.set_trace()
            return self.login()
        else:
            return self.driver.get_cookies()
        # except:
        #     return False
    def login(self):
        # self.driver.refresh()
        login_flag = False
        while not login_flag:
            time.sleep(15)
            self.driver.refresh()
            login_flag = json.loads(self.driver.find_element(By.XPATH, '//*[@id="input-params"]').get_attribute('data-session-status'))['authenticated']
        # pdb.set_trace()
        return self.driver.get_cookies()
class Task():
    def __init__(self,cookies,url_list,proxy,target):
        self.cookies = cookies
        self.url_list = url_list
        # self.lock = multiprocessing.Lock()
        self.proxy = proxy
        self.target = target
        # self.port = port
    def add_cookies(self):


        options = ChromeOptions()
        options.add_argument('--proxy-server={0}'.format(self.proxy.proxy))
        options.add_argument('--ignore-ssl-errors=yes')
        options.add_argument('--ignore-certificate-errors')
        # if headless:
        #     options.add_argument('--headless')
        options.add_experimental_option("excludeSwitches",
                                        ['enable-automation', 'enable-logging'])
        self.driver = webdriver.Chrome(executable_path=os.path.join(os.getcwd(),'chromedriver.exe'),options=options)


        self.driver.get('https://midway-auth.amazon.com/login')
        for cookie in self.cookies:
            self.driver.add_cookie(cookie)

    def elaine_searching(self,get_cookie_q,task_complete_queue):
        #@todo 如果碰到AEA，则让进程结束，用Queue
        #https://stackoverflow.com/questions/32053618/how-to-to-terminate-process-using-pythons-multiprocessing
        self.driver.set_page_load_timeout(20)
        get_url_fail_list = []
        maximum_fail_time = 10
        def get_elaine_response(try_times):
            # lock.acquire()
            while try_times < 2:
                try_times += 1
                try:
                    # ele = self.driver.find_elements_by_xpath("//div[@class='awsui-util-container-header']/h2")
                    ele = WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='app']/awsui-app-layout/div/main/div/div[2]/div/span/div/div/awsui-form/div/div[4]/span/div/awsui-button[1]/button/awsui-icon/span")))
                except:
                    ele = ''
                # ele = self.driver.wait_until_located("//div[@class='awsui-util-container-header']/h2")
                if ele=='':
                    try:
                        self.driver.refresh()
                    except:
                        pass
                else:
                    break


        for url in self.url_list:
            print(self.url_list.index(url))
            try:
                self.driver.get(url)
                print('getting url done')
            except:
                print('fail getting url')
                get_url_fail_list.append(1)
                if len(get_url_fail_list)>maximum_fail_time:
                    print('maximum failure time: '+str(maximum_fail_time)+' has reached')
                    break



            try:
                self.driver.find_element_by_xpath('//*[@id="posture-cookie-instructions"]/h1')
                # q.put('kill workers')
                print('AEA cookie expired')
                try:
                    get_cookie_q.put('get cookie',timeout=1)
                except queue.Full:
                    print('cookie queue is full')
                break
            except:
                # q.put('working')
                print('no AEA problem')
                pass
            try:
                not_responding_tag = self.driver.find_element_by_xpath('/html/body/div[1]/div[1]/div[2]/h1/span').text
                if not_responding_tag =='无法访问此网站':
                    print('Network problem')
                    break
            except:
                print('no network problem')
                pass
            print(url)
            # ele = self.driver.wait_until_located("//div[@class='awsui-util-container-header']/h2")
            get_elaine_response(0)
        try:
            task_complete_queue.put('task done',timeout=1)
        except queue.Full:
            pass
        self.driver.quit()
        print('chrome quit successfully')
        # result = self.proxy.har
        # self.write_result_to_file(str(result))
    def close(self):
        self.driver.quit()
        print('chrome quit successfully')
        # self.proxy.close()
        # self.server.stop()
    def write_result_to_file(self,result):
        lock.acquire()
        with open('har result.txt','a',encoding='utf-8') as f:
            f.write(result)
        lock.release()

def worker_job(param_list):
    url_list, proxy, target,task_complete_queue,get_cookie_q = param_list

    cookies = ast.literal_eval(open('cookies.txt','r').read())

    task = Task(cookies,url_list,proxy,target)
    task.add_cookies()
    # time.sleep(100)
    task.elaine_searching(get_cookie_q,task_complete_queue)
    task.close()
    # task.write_result_to_file()

def get_new_cookies():
    # while True:
        # time.sleep(400)
    print('getting new cookie')
    login = Login()
    cookies = login.check_if_login()
    login.driver.quit()
    with open('cookies.txt',mode='w') as f:
        f.write(str(cookies))


def assign_urls(asins_list,source,worker_num):
    base_url = 'https://prod.elaine.exporteligibility.amazon.dev/lookup/GlobalStore/'+source+'/'
    url_list = []
    asin_num_in_each_url = 8
    url_num = math.ceil(len(asins_list)/asin_num_in_each_url)
    for url_index in range(url_num):
        url_list.append(base_url+'%250A'.join(asins_list[url_index*asin_num_in_each_url:(url_index+1)*asin_num_in_each_url]))

    total_url_num = len(url_list)
    url_num_in_each_group = math.ceil(total_url_num/worker_num)
    url_list_list = []
    for i in range(worker_num):
        url_list_list.append(url_list[i*url_num_in_each_group:(i+1)*url_num_in_each_group])
    # pdb.set_trace()
    return url_list_list

def assign_params_to_each_worker(url_list_list,proxy,target,task_complete_queue,get_cookie_q):
    param_list = []
    for index in range(len(url_list_list)):
        param_list.append([url_list_list[index],proxy,target,task_complete_queue,get_cookie_q])
    # pdb.set_trace()
    return param_list

def init_pool_processes(the_lock):
    global lock
    lock = the_lock

def write_result_to_file(result):
    with open('har result.txt','a',encoding='utf-8') as f:
        f.write(result)
def process_response(result, source_mp,target):

    lines = []
    dedup_list = []
    mapping_fmid = {'US': ['1243749050', '192102097102', '-'],
                    'GB': ['832676903', '286380655902', '-'],
                    'DE': ['832676903', '286383074302', '-'], 'JP': ['540342884', '-'],
                    'AE': ['18034144125', '-']}
    def get_contribution_detail(contributions, rest_type):
        other_lines = []
        for contribution in contributions['contributions']:

            try:
                contribution_name = contribution['contributorName']
                if 'overrideRestriction' in contribution:
                    override = contribution['overrideRestriction']
                    try:
                        if (override['overrideType'] == 'ENABLE') and (target in override['overrideCountries']):
                            continue
                    except: # 这里有两种可能
                        if (override['overridePermissionType'] == 'ENABLE') and (target in override['overrideDestinationCountries']):
                            continue
                if rest_type in contribution:
                    contribution_detail = contribution[rest_type]
                else:
                    contribution_detail = contribution['missingOfferRestriction']
                if contribution_detail['exportRestrictions']:

                    export_restrictions = contribution_detail['exportRestrictions']
                    for export_restriction in export_restrictions:

                        if 'restrictedCountries' in export_restriction:
                            restrict_country = export_restriction['restrictedCountries']

                            restrict_country = str(restrict_country)
                            restrictionType = str(export_restriction['restrictionType'])

                            if ((restrictionType == 'Restricted') and ((target in restrict_country)
                                                                       or ('ALL' in restrict_country))) or \
                                    ((restrictionType == "RestrictedAll_Except") and
                                     (target not in restrict_country)):
                                restrictionReasons = str(export_restriction['restrictionReasons']).replace('\t', '')
                                other_lines.append('\t'.join([contribution_name,
                                                              ' '.join([restrictionReasons, restrictionType,
                                                                        restrict_country])]))

            except Exception as e:
                print('Exception 2', e)

        return other_lines
    success_asin_list = []
    for entry in result['log']['entries']:
        url = entry['request']['url']
        if entry['request']['method'] == 'GET':
            if '/GlobalStoreRetail' in url:
                if entry['response']['status'] == 502:
                    pass
                other_lines = []
                _response = entry['response']

                try:
                    _content = _response['content']['text']
                    # if entry['response']['status']:
                    #     pattern = re.compile(r'"asin": "(.{1,10})"')
                    #     success_asin = re.search(pattern, _content)[0][9:][:-1]
                    #     program_pattern = re.compile(r'"program": "(.{1,17})"')
                    #     program = re.search(program_pattern, _content)[0][12:][:-1]
                    #     if program =='GlobalStoreRetail':

                    #         success_asin_list.append(success_asin)
                except:
                    _content = ''

                content_list = _content.split('\n')

                for con in content_list:
                    if '"marketplaceId"' in con:
                        current_mp = str(con.split(': ')[1].replace(',', ''))

                        break
                for con in content_list:
                    if '"asin"' in con:
                        current_asin = str(con.split(': ')[1].replace(',', '').replace('"',''))

                        break
                # pdb.set_trace()
                try:
                    if (current_asin + current_mp) in dedup_list:
                        continue
                    else:
                        dedup_list.append((current_asin + current_mp))

                    json_data = json.loads(_content)


                    for i in range(len(json_data)):
                        # try:
                        try:
                            merchantId = str(json_data[i]['merchantId'])
                        except:
                            merchantId = '-'

                        asin = str(json_data[i]['asin'])
                        if asin not in success_asin_list:
                            success_asin_list.append(asin)
                            print(asin)
                        try:
                            fmid = str(json_data[i]['fmid'])
                        except:
                            fmid = '-'
                        if fmid not in mapping_fmid[source_mp]:
                            continue
                        messages = str(json_data[i]['messages'])
                        asinExportability = json_data[i]['asinExportability']
                        offerExportability = json_data[i]['offerExportability']

                        # asin_ineligibleCountries = asinExportability['ineligibleCountries']

                        other_lines = get_contribution_detail(asinExportability, 'asinRestriction')
                        offer_other_lines = get_contribution_detail(offerExportability, 'offerRestriction')
                        other_lines.extend(offer_other_lines)

                        for line in other_lines:

                            # self.write_to_result('\t'.join([merchantId,asin,fmid])
                            # +'\t'+line)
                            lines.append(tuple([source_mp, merchantId, asin, fmid] + line.split('\t')))
                except:
                    pass

    return [lines,success_asin_list]

def get_partial_result(asin_list,source,subprocess_num,search_time,target,pool):
    if asin_list !=[]:
        if search_time>=0:
            url_list_list = assign_urls(asin_list, source, subprocess_num)
            # port_list = [8081,8083]
            server_loc = r'browsermob-proxy-2.1.4\bin\browsermob-proxy.bat'
            server = Server(
                server_loc, \
                options={'port': 8081})
            server.start()
            proxy = server.create_proxy()
            #直接开个进程，一直刷cookies
            proxy.new_har("elaine", options={'captureHeaders': False, 'captureContent': True})
            param_list = assign_params_to_each_worker(url_list_list, proxy, target)
            # cookies_list = [cookies for i in range(subprocess_num)]
            # pdb.set_trace()



            # 给execution传cookies;每个worker要做的link

            pool.map(worker_job, param_list)

            result = proxy.har
            # write_result_to_file(str(result))
            result,asin_has_result_list = process_response(result, source, target)
            df = pd.DataFrame(result, columns=['source_mp', 'merchantId', 'asin', 'fmid', 'contribution_name',
                                               'contribution_content'])
            df_list = []
            df_list.append(df)
            full_df = pd.concat(df_list, sort=False)
            full_df.drop_duplicates(inplace=True)
            full_df['source_mp'] = full_df['source_mp'].apply(lambda x: 'UK' if x == 'GB' else x)
            full_df.to_csv('elaine_output' + '.csv', index=False, mode='a')
            t2 = time.time()

            print(search_time)
            proxy.close()
            server.stop()
            print(asin_has_result_list)
            print(len(asin_has_result_list))

            search_time -=1
        else:
            return 0
    else:
        return 0

def watch(get_cookie_q):
    while True:
        time.sleep(10)
        try:
            msg = get_cookie_q.get(timeout=50)
        except queue.Empty as e:
            msg = ''
        except EOFError:
            break
        print(msg)
            # get_new_cookies()
        if msg=='get cookie':
            get_cookie_q.put('waiting')
            # get_new_cookies()
            break

def execution(param_list):
    t3 = time.time()
    task_complete_queue = param_list[0][3]
    # q = param_list[0][3]
    # get_cookie_q = param_list[0][4]
    # l = multiprocessing.Lock()
    # pool = Pool(processes=subprocess_num, initializer=init_pool_processes, initargs=(l,))
    # watcher = multiprocessing.Process(target=watch, args=(get_cookie_q,))
    # watcher.daemon = True
    # watcher.start()
    pool = Pool(processes=subprocess_num,maxtasksperchild=1)
    result = pool.map_async(worker_job, param_list)
    result.get()
    pool.close()
    pool.join()
    t4 = time.time()
    print(str(t4-t3)+' seconds used searching')
    # time.sleep(10)


    # while True:
        # if not q.empty():
        #
        #     msg = q.get()
        #     print(msg)
        #     if msg == 'kill workers':
        #
        #         pool.close()
        #         subprocess.call("TASKKILL /f  /IM  CHROME.EXE")
        #         subprocess.call("TASKKILL /f  /IM  CHROMEDRIVER.EXE")
        #         watcher.close()
        #         print('watcher close executed; pool close executed')
        #         break
        # if task_complete_queue.full():
        #     print('task complete')
        #     while not task_complete_queue.empty():
        #         print(task_complete_queue.get())
        #     break
    if task_complete_queue.full():
        while not task_complete_queue.empty():
            print(task_complete_queue.get())
        print('task complete')



    result = proxy.har

    # write_result_to_file(str(result))
    result, asin_has_result_list = process_response(result, source, target)
    df = pd.DataFrame(result, columns=['source_mp', 'merchantId', 'asin', 'fmid', 'contribution_name',
                                       'contribution_content'])

    return df,asin_has_result_list
    # df_list = []
    # df_list.append(df)
    # full_df = pd.concat(df_list, sort=False)
    # full_df.drop_duplicates(inplace=True)
    # full_df['source_mp'] = full_df['source_mp'].apply(lambda x: 'UK' if x == 'GB' else x)
    # elaine_output_path = '/'.join([os.getcwd(), 'elaine_output.csv'])
    # full_df.to_csv(elaine_output_path, index=False, mode='w')
    # t2 = time.time()

def elaine_result_process(result,target):
    result = result.astype(object)
    result['ASIN'] = result['asin']
    result['Source'] = result['source_mp']
    result['Target'] = target
    result['Blocker content'] = result['contribution_content']
    result['Blocker'] = ''
    result['Tracker'] = ''
    for index, row in result.iterrows():
        row['Blocker'] = blocker_mapping(row['contribution_name'], row['contribution_content'])
        row['Tracker'] = tracker_mapping(row['Blocker'], row['Blocker content'], row['Source'])

    return result.loc[:, ['ASIN', 'Source', 'Target', 'Blocker', 'Blocker content', 'Tracker']]

def blocker_mapping(blocker, blocker_content):
    if blocker == 'DropshipRestrictions':
        blocker_map = 'Dropship'
    elif blocker == 'PricingRestrictions':
        blocker_map = 'Pricing Restrictions'
    elif blocker == 'PrivateBrand':
        blocker_map = 'Private label'
    elif blocker in ('BusinessRule','OperationalRule'):
    # elif blocker == 'BusinessRule':
        if ('jp_too_heavy' in blocker_content.lower()) or ('jp_trans_itemtoolarge_all' in blocker_content.lower()):
            blocker_map = 'BusinessRule_nonaction'
        elif ("not_conveyable" in blocker_content.lower()) or ('missing_size_or_weight' in blocker_content.lower()):
            blocker_map = 'BusinessRule_Not_Conveyable'
        elif "BISS" in blocker_content:
            blocker_map = 'BusinessRule_BISS'
        elif ("shelf_life" in blocker_content.lower()) or ("shelflife" in blocker_content.lower()) or (
                "shellife" in blocker_content.lower()):
            blocker_map = 'BusinessRule_Shelf_life'
        elif ("too_large" in blocker_content.lower()) or ("gb_oversize" in blocker_content.lower()) or (
                "de_oversize" in blocker_content.lower()):
            blocker_map = 'BusinessRule_Too_Large'
        elif ("too_heavy" in blocker_content.lower()) or ('gb_overweight' in blocker_content.lower()) or (
                "de_overweight" in blocker_content.lower()):
            blocker_map = 'BusinessRule_Too_Heavy'
        else:
            blocker_map = 'BusinessRule_nonaction'
    elif blocker == 'VendorRestrictions':
        blocker_map = 'vendor brand restriction'
    elif blocker == 'GlobalStoreRetailBusinessRuleRestrictions':
        if ('retail_restrict_deprecated_retail_seller_of_record_vendor_id' in blocker_content.lower()) or (
                'retail_restrict_brand_vendor' in blocker_content.lower()):
            blocker_map = 'vendor brand restriction'
        elif 'ineligibleforagl' in blocker_content.lower():
            blocker_map = 'Amazon Global Listings'
        elif 'retail_restrict_future_launch_date_items' in blocker_content.lower():
            blocker_map = 'Pre-Order'
        elif ('retail_restrict_subcat' in blocker_content.lower()) or (
                "retail_block_unscored_gl" in blocker_content.lower()) or (
                "retail_block_unscored_gls" in blocker_content.lower()) or (
                'retail_block_unscored_subcat' in blocker_content.lower()):
            blocker_map = 'unapproved subcategory'
        else:
            blocker_map = 'Offer-level Business'
    elif blocker == 'HazmatRule':
        blocker_map = 'HazmatRule'
    elif blocker == 'PolicyManager':
        blocker_map = 'PolicyManager'
    elif blocker == 'TradeAuthority':
        blocker_map = 'TradeAuthority'
    elif blocker == 'ListingPolicy':
        blocker_map = 'RP Restriction'
    elif blocker == 'HtsClassification':
        blocker_map = 'HtsClassification'
    elif blocker == 'ProductType':
        blocker_map = 'ProductType'
    else:
        blocker_map = 'Undefined blocker'
        print('Warning: Elaine blocker', blocker, 'could not be identified')
    return blocker_map

def tracker_mapping(blocker, blocker_content, source):
    if blocker in ['Dropship', 'Pricing Restrictions', 'Private label', 'BusinessRule_nonaction', 'ProductType',
                   'vendor brand restriction', 'Amazon Global Listings', 'Pre-Order', 'Offer-level Business']:
        tracker = 'non_action'
    elif blocker in ['unapproved subcategory', 'BusinessRule_BISS', 'BusinessRule_Not_Conveyable', 'HtsClassification',
                    'BusinessRule_Too_Heavy', 'BusinessRule_Too_Large', 'HazmatRule', 'PolicyManager']:
        tracker = 'Appeal Tracker'
    elif blocker in ['BusinessRule_Shelf_life']:
        tracker = 'Pending submitting to POC'
    elif blocker == 'TradeAuthority' and source in ['JP']:
        tracker = 'Pending submitting to POC'
    elif blocker == 'TradeAuthority' and source in ['US', 'UK', 'GB', 'DE', 'AE']:
        tracker = 'Appeal Tracker'
    elif blocker == 'RP Restriction' and 'voltage' in blocker_content.lower():
        tracker = 'Need backfill Voltage'
    elif blocker == 'RP Restriction' and 'voltage' not in blocker_content.lower():
        tracker = 'Appeal Tracker'
    else:
        tracker = 'Warning: Undefined tracker'
        print('Warning: Tracker for', blocker, blocker_content, 'could not be identified')

    return tracker
if __name__ == '__main__':
    #@todo 目前只支持asin_elaine.xlsx中放一个source
    # start_monitoring(seconds_frozen=20, test_interval=100)
    # target = 'IT'
    t1 = time.time()
    manager = multiprocessing.Manager()
    q = manager.Queue()
    get_cookie_q = manager.Queue(1)

    login = Login()
    cookies = login.check_if_login()
    with open('cookies.txt', mode='w') as f:
        f.write(str(cookies))

    login.driver.quit()

    subprocess_num = 4
    task_complete_queue = manager.Queue(subprocess_num)
    # 这个工具聚焦在一个source-target，将ASINs分成每20个放到一个link里，根据worker数量进行分组
    df = pd.read_excel('asin_elaine.xlsx')
    source = df['source'].unique()[0]
    target = df['target'].unique()[0]
    df['asin'] = df['asin'].map(lambda x: str(x).zfill(10))
    asin_list = df['asin'].unique().tolist()
    asin_count = len(asin_list)
    search_time = math.ceil(asin_count / 1500) + 1
    # url_list_list = assign_urls(asin_list, source, subprocess_num)
    # port_list = [8081,8083]
    # server_loc = r'browsermob-proxy-2.1.4\bin\browsermob-proxy.bat'
    # server = Server(
    #     server_loc, \
    #     options={'port': 8081})
    # server.start()
    # proxy = server.create_proxy()
    # proxy.new_har("elaine", options={'captureHeaders': False, 'captureContent': True})
    # param_list = assign_params_to_each_worker(url_list_list, proxy, target, q,get_cookie_q,task_complete_queue)
    # search_time = 16
    add_column_mark = search_time
    # final_df = pd.DataFrame(columns=['source_mp', 'merchantId', 'asin', 'fmid', 'contribution_name',
    #                                    'contribution_content'])
    # asin_has_result_df, asin_has_result_list = execution(param_list)
    # asin_has_no_result_list = list(set(asin_list) - set(asin_has_result_list))
    # final_df = final_df.append(asin_has_result_df, ignore_index=True)
    asin_has_no_result_list = asin_list
    elaine_output_path = '/'.join([os.getcwd(), 'elaine_output.csv'])
    elaine_output_processed_path = '/'.join([os.getcwd(), 'elaine_output_processed.csv'])
    try:
        os.remove(elaine_output_path)
        os.remove(elaine_output_processed_path)
    except:
        pass
    while search_time >0:
        # server_loc = r''
        server_loc = '\\'.join([os.getcwd(), r'browsermob-proxy-2.1.4\bin\browsermob-proxy.bat'])
        # pdb.set_trace()
        print(server_loc)
        server = Server(
            server_loc, \
            options={'port': 8081})
        server.start()
        proxy = server.create_proxy()
        proxy.new_har("elaine", options={'captureHeaders': False, 'captureContent': True})
        print(len(asin_has_no_result_list))
        print(asin_has_no_result_list)
        if asin_has_no_result_list != []:
            if get_cookie_q.empty():
                get_cookie_signal = 'no'
                pass
            else:
                get_cookie_signal = get_cookie_q.get()
            # if get_cookie_signal == 'waiting':
            if get_cookie_signal == 'get cookie':
                get_new_cookies()
                time.sleep(10)
            print(get_cookie_signal)
            print(search_time)

            remnant_url_list_list = assign_urls(asin_has_no_result_list, source, subprocess_num)
            # proxy.new_har("elaine", options={'captureHeaders': False, 'captureContent': True})
            param_list = assign_params_to_each_worker(remnant_url_list_list, proxy, target,task_complete_queue,get_cookie_q)
            asin_has_result_df, asin_has_result_list = execution(param_list)
            asin_has_no_result_list = list(set(asin_has_no_result_list) - set(asin_has_result_list))
            # final_df = final_df.append(asin_has_result_df, ignore_index=True)
            asin_has_result_df.drop_duplicates(inplace=True)
            asin_has_result_df['source_mp'] = asin_has_result_df['source_mp'].apply(lambda x: 'UK' if x == 'GB' else x)
            if add_column_mark == search_time:
                asin_has_result_df.to_csv(elaine_output_path, index=False, mode='a')
                asin_has_result_df = elaine_result_process(asin_has_result_df, target)
                asin_has_result_df.drop_duplicates(inplace=True)
                asin_has_result_df.to_csv(elaine_output_processed_path, index=False, mode='a')
            else:
                asin_has_result_df.to_csv(elaine_output_path, index=False, mode='a',header=False)
                asin_has_result_df = elaine_result_process(asin_has_result_df, target)
                asin_has_result_df.drop_duplicates(inplace=True)
                asin_has_result_df.to_csv(elaine_output_processed_path, index=False, mode='a',header=False)
            search_time -= 1
        else:
            break
        proxy.close()
        server.stop()
        os.system('taskkill /f /im java.exe')
        os.system('TASKKILL /f /IM CHROME.EXE')
        os.system('"TASKKILL /f /IM CHROMEDRIVER.EXE"')
    # final_df.drop_duplicates(inplace=True)
    # final_df['source_mp'] = final_df['source_mp'].apply(lambda x: 'UK' if x == 'GB' else x)
    # elaine_output_path = '/'.join([os.getcwd(), 'elaine_output.csv'])
    # final_df.to_csv(elaine_output_path, index=False, mode='w')
    # proxy.close()
    # server.stop()
    # subprocess.call("TASKKILL /f  /IM  CHROME.EXE")
    # subprocess.call("TASKKILL /f  /IM  CHROMEDRIVER.EXE")
    t2 = time.time()
    print(t2-t1)