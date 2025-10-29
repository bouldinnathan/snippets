#This is a file for easy imports and easy threading
#version 0.7.7

#function of import and install
# Easy_installer.easy("flask") Easy_installer.easy("https://github.com")
import os
import subprocess
class Easy_installer:
    
    def __init__(self):
        import subprocess
        try:
            MAX_PATH = int(subprocess.check_output(['getconf', 'PATH_MAX', '/']))
        except (ValueError, subprocess.CalledProcessError, OSError):
            try:
                deprint('calling getconf failed - error:', traceback=True)
                MAX_PATH = 4096
            except:
                pass
                #print("MAX_PATH had and issue...")
        try:_=os.system("sudo apt -y install python3-pip")
        except:pass
        try:_=os.system("sudo apt -y install git")
        except:pass
        try:_=os.system("sudo apt -y install python3-dev ")
        except:pass
        try:_=os.system("sudo apt -y install python3-full ")
        except:pass
        
    
    
    def install_and_import(self,package):
        import warnings
        try:
            import importlib
            try:
                importlib.import_module(package)
                return 
            except ImportError:
                import pip
                try:
                    from pip._internal import main
                except ImportError:
                    warnings.warn("Warning "+"Failed to import pip")
                    try:
                        from pip import main
                    except ImportError:
                        warnings.warn("Warning "+"Failed to import pip")
                        from pip import __main__
                        warnings.warn("imported pip")
                        
                print("installing: "+package)
                try:
                    main(['install', package])
                    globals()[package] = importlib.import_module(package)
                except:
                    main(['install',"--no-cache-dir","--break-system-packages", package])
                    
            finally:
                globals()[package] = importlib.import_module(package)
        except:
            warnings.warn("Warning "+str(package)+" might not have been installed. Check that lastest pip is installed")
            
            
        
    def install_and_import_special(self,url,command=None):
        #self.install_and_import("gitpython")
        #from git import Repo
        try:os.system("git clone "+url)
        except:pass
        self.install_and_import("warnings")
        
        #Repo.clone_from(url, '''''')
        
        if not type(command)==type(None):
            os.chdir(url.split('/')[-1].replace(".git",""))
            os.system(command)
        else:warnings.warn("No install command for: "+str(url))
        

    def easy(self,url,import_name=None,easy_command=None):
        if ("http" in url or "www." in url) and type(import_name)==type(None) and not type(easy_command)==type(None):
            self.install_and_import_special(url,command=easy_command)
        elif not type(import_name)==type(None) and type(easy_command)==type(None):
            try:self.install_and_import(import_name)
            except:self.install_and_import(url)
            self.install_and_import(import_name)
        elif not type(import_name)==type(None) and not type(easy_command)==type(None):
            self.install_and_import_special(url,command=easy_command)
            self.install_and_import(import_name)
        else:
            self.install_and_import(url)
            
            
            



################################################################################
# generic_threader takes the name of your function and a list of all your data
# the list is iterated into the your function
# once all data is process the full data is returned
# data must be returned by the function to be threaded
def target(conn,funtion_to_thread,tuple_of_data,qu_bool=False):
    #print("target",flush=True)
    #print("target qu_bool: "+str(qu_bool),flush=True)
    if qu_bool:
        _=funtion_to_thread(tuple_of_data)
        #print(_,flush=True)
        conn.put(_)
    else:
        conn.send(funtion_to_thread(tuple_of_data))
        conn.close()
        
def cpuChk(seconds):
    import time
    try:
        import psutil
    except:
        return None
    if psutil.LINUX:
        # Linux-specific code
        return psutil.cpu_percent(interval=seconds)
    elif psutil.WINDOWS:
        # Windows-specific code
        return psutil.cpu_percent(interval=seconds)
    else:
        return None  # Unsupported platform

def generic_threader(function_name,datas,thread_count=16,max_cpu_percent=80,cpu=False,qu_bool=False):    
    #import zipfile
    import os
    from threading import Thread
    from  multiprocessing import Pipe
    from  multiprocessing import Process# remove if bad
    import multiprocessing
    from  multiprocessing import Queue# remove if bad

    qu = Queue()

    
    #import shutil


    #def target(conn,funtion_to_thread,tuple_of_data):
    #    conn.send(funtion_to_thread(tuple_of_data))
        
    total_processed=0     
    count=0
    current_working_threads=[]

    all_threads_datas=[]

    total_amount_of_data=len(datas)
    for data in datas:
        count+=1
        total_processed=+1
        
        parent_conn, child_conn =Pipe()
        
        if cpu==True and qu_bool==True:
            print("Windows box may not work... TODO: add core adjusted affenity")
            t = Process(target=target, args=(qu, function_name, data,qu_bool))
            current_working_threads.append((t,qu,qu_bool))
        elif cpu==True and qu_bool==False:
            print("Windows box may not work... TODO: add core adjusted affenity")
            t = Process(target=target, args=(child_conn, function_name, data,qu_bool))
            current_working_threads.append((t,parent_conn,qu_bool))
        elif cpu==False and qu_bool==False:
            t = Thread(target=target, args=(child_conn, function_name, data,qu_bool))
            current_working_threads.append((t,parent_conn,qu_bool))
        elif cpu==False and qu_bool==True:
            t = Thread(target=target, args=(qu, function_name, data,qu_bool))
            current_working_threads.append((t,qu,qu_bool))
            
        if max_cpu_percent != 0:
            if type(cpuChk(.2))!=type(None) and type(max_cpu_percent)!=type(None):
                while cpuChk(.2) >= max_cpu_percent: pass
        t.start()
            

        # limits Number of threads by forcing join every time thread count is a multible of thread_count
        if count%thread_count==0 or count>=total_amount_of_data:

            # collects all of the data to be return at the end
            for t,parent_conn,qu_bool in current_working_threads:
                if qu_bool:
                    while not parent_conn.empty():
                        all_threads_datas.append(parent_conn.get())
                else:
                    all_threads_datas.append(parent_conn.recv())
                t.join()
                
            # garbage collection
            current_working_threads=[]

        # just for updating user
        if total_processed%10==0:
            print("Total Processed: "+str(total_processed))
            
    # collects the rest of the data to be return at the end
    for t,parent_conn,child_conn in current_working_threads:
        all_threads_datas.append(parent_conn.recv())
        t.join()
        
    # garbage collection
    current_working_threads=[]
    print("Total Processed: "+str(len(datas)))
    return all_threads_datas

def gt(function_name,datas,thread_count=16,max_cpu_percent=80,cpu=False,qu_bool=False): # shorthand
    return generic_threader(function_name,datas,thread_count=thread_count,max_cpu_percent=max_cpu_percent,cpu=cpu,qu_bool=qu_bool)    
                
###########################################################################
# this is used to read almost any text file with its correct charset
# given file location and optional check regular expression or
# number of requested charectors if the file is large
def read_file(file_loc,number_of_char=True, check_re=""):

    def checker2(text):
        from bs4 import BeautifulSoup
        #print(text)
        soup = BeautifulSoup(text, 'html.parser')
        title = soup.find('title')
        #print(title)
        #print(title.string)
        if title==None:
            return False
        if title.string=="":
            return False
        return True


    # this give a check only if upper function gives string
    def checker(re_data,text):
        if re_data=="":
            return True
        title=re.findall(re_data,text)
        
        if title==[]:
            if checker2(text):
                return True
            print("More Char are needed....")
            return False
        return True
        
    
    encodings=["UTF-8","ANSI","ascii","iso-8859-1","646"," us-ascii","big5","big5-tw"," csbig5","big5hkscs","big5-hkscs"," hkscs","cp037","IBM037"," IBM039","cp273","273"," IBM273"," csIBM273","cp424","EBCDIC-CP-HE"," IBM424","cp437","437"," IBM437","cp500","EBCDIC-CP-BE"," EBCDIC-CP-CH"," IBM500","cp720","cp737","cp775","IBM775","cp850","850"," IBM850","cp852","852"," IBM852","cp855","855"," IBM855","cp856","cp857","857"," IBM857","cp858","858"," IBM858","cp860","860"," IBM860","cp861","861"," CP-IS"," IBM861","cp862","862"," IBM862","cp863","863"," IBM863","cp864","IBM864","cp865","865"," IBM865","cp866","866"," IBM866","cp869","869"," CP-GR"," IBM869","cp874","cp875","cp932","932"," ms932"," mskanji"," ms-kanji","cp949","949"," ms949"," uhc","cp950","950"," ms950","cp1006","Urdu","cp1026","ibm1026cp1125","1125"," ibm1125"," cp866u"," ruscii","cp1140","ibm1140","cp1250","windows-1250","cp1251","windows-1251"," Macedonian","cp1252","windows-1252","cp1253","windows-1253","Greek","cp1254","windows-1254","cp1255","windows-1255","Hebrew","cp1256","windows-1256","Arabic","cp1257","windows-1257","cp1258","windows-1258","cp65001","CP_UTF8","euc_jp","eucjp"," ujis"," u-jis","euc_jis_2004","jisx0213"," eucjis2004","euc_jisx0213","eucjisx0213","Japanese","euc_kr","euckr"," ksc5601"," ks_c-5601"," ks_c-5601-1987"," ksx1001"," ks_x-1001","gb2312","chinese"," csiso58gb231280"," euc-cn"," euccn"," eucgb2312-cn"," gb2312-1980"," gb2312-80"," iso-ir-58","gbk","936"," cp936"," ms936","gb18030","gb18030-2000","hz","hzgb"," hz-gb"," hz-gb-2312","iso2022_jp","csiso2022jp"," iso2022jp"," iso-2022-jp","iso2022_jp_1","iso2022jp-1"," iso-2022-jp-1","iso2022_jp_2","iso2022jp-2"," iso-2022-jp-2"," Greek","iso2022_jp_2004","iso2022jp-2004"," iso-2022-jp-2004","iso2022_jp_3","iso2022jp-3"," iso-2022-jp-3","iso2022_jp_ext","iso2022jp-ext"," iso-2022-jp-ext","iso2022_kr","csiso2022kr"," iso2022kr"," iso-2022-kr","latin_1","iso-8859-1"," iso8859-1"," 8859"," cp819"," latin"," latin1"," L1","iso8859_2","iso-8859-2"," latin2"," L2","iso8859_3","iso-8859-3"," latin3"," L3","Esperanto"," Maltese","iso8859_4","iso-8859-4"," latin4"," L4","iso8859_5","iso-8859-5"," cyrillic","Bulgarian"," Byelorussian"," Macedonian","iso8859_6","iso-8859-6"," arabic","Arabic","iso8859_7","iso-8859-7"," greek"," greek8","Greek","iso8859_8","iso-8859-8"," hebrew","Hebrew","iso8859_9","iso-8859-9"," latin5"," L5","iso8859_10","iso-8859-10"," latin6"," L6","iso8859_11","iso-8859-11"," thai","iso8859_13","iso-8859-13"," latin7"," L7","iso8859_14","iso-8859-14"," latin8"," L8","iso8859_15","iso-8859-15"," latin9"," L9","iso8859_16","iso-8859-16"," latin10"," L10","johab","cp1361"," ms1361","koi8_r","koi8_t","Tajik","koi8_u","kz1048","kz_1048"," strk1048_2002"," rk1048","Kazakh","mac_cyrillic","maccyrillic"," Byelorussian"," Macedonian","mac_greek","macgreek","Greek","mac_iceland","maciceland","mac_latin2","maclatin2"," maccentraleurope","mac_roman","macroman"," macintosh","mac_turkish","macturkish","ptcp154","csptcp154"," pt154"," cp154"," cyrillic-asian","shift_jis","csshiftjis"," shiftjis"," sjis"," s_jis","shift_jis_2004","shiftjis2004"," sjis2004","shift_jisx0213","shiftjisx0213"," sjisx0213"," s_jisx0213","utf_32","U32"," utf32","","utf_32_be","UTF-32BE","utf_32_le","UTF-32LE","utf_16","U16"," utf16","utf_16_be","UTF-16BE","utf_16_le","UTF-16LE","utf_7","U7"," unicode-1-1-utf-7","utf_8","U8"," UTF"," utf8","utf_8_sig"]
    #encodings=["UTF-8"]

    for encoding in encodings:
        try:
            
            file=open(file_loc,"r",encoding=encoding)
            
            if number_of_char==True:
                text=file.read()

                #only return full text if the check returns True only. True is returned if no check is given
                if checker(check_re,text):
                    return text
                
            else:
                text=file.read(number_of_char)
                
                if checker(check_re,text):
                    return text
        except UnicodeDecodeError:
            pass
        except LookupError:
            pass
        except Exception as e:
            print(e)
            pass
    
    #print( str(file_loc)+" : No Text encoding found")
    #raise Exception (str(file_loc)+" : No Text encoding found")
    return ""


###################################################################################################################
#             Simple API Generator Creator
# Add one item to be processed at a time with a "url" "headers" and a minimum "timer" between call to rate limit
# Add_list add all item to be processed at the same time [{"url":url,"headers":headers,"timer",timer},...]
# Call_api is a generator that yeild the data as a json one at a time
# Get returns the same infomation as yeild just with a simple return
#
###################################################################################################################
class api_gen:
    #api_data={}
    apis=[]
    get_first_run=True
    get_next=None


    def __init__(self):
        self.get_first_run=True
        self.get_next=None
        self.apis=[]
        pass


    #this function creates a generator that yeld 
    def add(self,url,headers="",timer=0):
        api_data={"url":url,"headers":headers,"timer":timer}
        self.apis.append(api_data)

    def add_list(self,api_data_list):
        self.apis.extend(api_data_list)#[{"url":url,"headers":headers,"timer",timer},...]

    def call_api (self):
        from time import sleep 
        import requests

        if len(self.apis)==0:
            yield None

        for api_data in self.apis:
            url=api_data["url"]
            headers=api_data["headers"]
            response = requests.get(url, headers=headers)
            data = response.json()

            sleep(api_data["timer"])
            yield data
        self.apis=[]

    def get(self):
        if self.get_first_run:    
            self.get_next=self.call_api()
            self.get_first_run=False
        try:
            return next(self.get_next)
        except StopIteration:
            return None
    def get_queue(self):
        return self.apis



###########################################################################
# this is used to make multithreaded calls to exchanges 
# these calls are not rate limited. This class depends of generic_threader
#

class Crypto:
    
    def __init__(self,):
        import asyncio
        import os
        import sys
        import platform
        
        if platform.system()=='Windows':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        sys.path.append(root + '/python')
        
        pass

    #simplified called by removing async
    def get_single_symbol_exchange(self,symbol,exchange_id):# 'binance','BTC/USDC'
        import asyncio
        import ccxt.async_support as ccxt
        
        async def get_single_symbol_exchange_async(symbol, exchange_id): # 'binance','BTC/USDC'
            try:
                exchange = getattr(ccxt, exchange_id)()
                ticker = await exchange.fetch_ticker(symbol)
                await exchange.close()
                return {exchange_id:ticker}
            except Exception as e:
                await exchange.close()
                return {exchange_id:None}
            return {exchange_id:None}
        
        return asyncio.run(get_single_symbol_exchange_async(symbol, exchange_id))#[('gate':{dict_returned})] or [('binance':None)]
        


    # this is the function used by generic threader to multi-thread
    def get_multiple_symbol_exchange_combined(self,data): #('binance','BTC/USDC') or ('gate','ETH/USDC')  
        symbol, exchange_id=data
        return self.get_single_symbol_exchange(symbol, exchange_id)#[('gate':{dict_returned})] or [('binance':None)]

    # this function increase types of inputs and prepares data for threading
    # Most external calls should be made here
    def get_simple(self,symbols, exchange_ids=None):#['BTC/USDC','ETH/USDC'],['gate','binance']
        import ccxt.async_support as ccxt

        
        if exchange_ids==None:exchange_ids=ccxt.exchanges # all exchanges are selected if no exchange is give
        datas=[]
        
        if (type(symbols)==type([]) or type(symbols)==type(())) and (type(exchange_ids)==type([]) or type(exchange_ids)==type(())):# only accepts two lists/tuples
            for symbol in symbols:
                for exchange_id in exchange_ids:
                    datas.append((symbol,exchange_id))
        if type(symbols)==type("") and (type(exchange_ids)==type([]) or type(exchange_ids)==type(())):# only accepts one string and one list/tuple
            symbol=symbols
            for exchange_id in exchange_ids:
                datas.append((symbol,exchange_id))
        if (type(symbols)==type([]) or type(symbols)==type(())) and type(exchange_ids)==type(""):# only accepts one list/tuple and one string
            exchange_id=exchange_ids
            for symbol in symbols:
                datas.append((symbol,exchange_id))
        if type(symbols)==type("") and type(exchange_ids)==type(""):# only accepts two strings
            exchange_id=exchange_ids
            symbol=symbols
            datas.append((symbol,exchange_id))
            
                         
        temp=easy_mode.generic_threader(self.get_multiple_symbol_exchange_combined,datas)
        return temp #[('gate':{dict_returned}),('binance':None)]

    def get_exchanges():
        import ccxt.async_support as ccxt
        return ccxt.exchanges

    def help():
        temp="get_exchanges() returns list of exchanges get_simple returns data on symbols from exchanges symbols='' or [] exchange_ids='' or [] or None(default)"
        print(temp)
        return temp



def move_contents_up_one_level(directory,replace=True):
    """
    Move all files and folders within the given directory up one level.
    
    :param directory: The directory whose contents are to be moved.
    """
    easy=Easy_installer()#required to make class
    easy.easy("shutil")
    import shutil
    import os
    # Check if directory exists and is a directory
    if not os.path.exists(directory) or not os.path.isdir(directory):
        raise ValueError(f"'{directory}' is not a valid directory path.")
    
    parent_directory = os.path.dirname(directory)
    
    # If the parent directory is same as the directory, it means the directory is a root directory
    if parent_directory == directory:
        raise ValueError(f"Can't move files and folders up from the root directory: {directory}")
    
    for item_name in os.listdir(directory):
        item_path = os.path.join(directory, item_name)
        destination_path = os.path.join(parent_directory, item_name)

        # If a file/folder with the same name already exists in the destination, rename the item to avoid conflict
        counter = 1
        while os.path.exists(destination_path) and not replace:
            base, extension = os.path.splitext(item_name)
            if os.path.isdir(item_path):  # if the item is a folder
                new_name = f"{base}_{counter}"
            else:  # if the item is a file
                new_name = f"{base}_{counter}{extension}"
            destination_path = os.path.join(parent_directory, new_name)
            counter += 1

        shutil.move(item_path, destination_path)



    
###########################################################################
# this is used to make download the newest driver for chrome for selenium
# This function depends of easy_installer/download_files/flatten to download correct import zipfile and process.
# return list of possible exicutibles depending on import platform and tries 
# to return only one. ["chrome.exe"]
def download_file(url):
    import requests
    local_filename = url.split('/')[-1]
    # NOTE the stream=True parameter below
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): 
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                #if chunk: 
                f.write(chunk)
    return local_filename

def flatten(l):
    return [item for sublist in l for item in sublist]

def selenium_prep(version="Latest"):
    easy=Easy_installer()
    import requests
    try:import platform
    except:easy.easy("platform")
    import sys
    try:from selenium import webdriver
    except:
        easy.easy("selenium")
        from selenium import webdriver

    try:version_num=int(version.split(".")[0])
    except:version_num=9999999

    #print(version_num)
    driver="chromedriver.exe"

    def _check(driver_loc="chromedriver.exe"):

        try:
            driver_loc="chromedriver.exe"
            temp_driver=webdriver.Chrome(driver_loc)
            temp_driver.quit()
            return True
        except:
            return False

    if _check():
        print("Download was skipped...")
        return webdriver.Chrome(driver)
    
    #import Easy_installer #only require if function is not in easymode
    easy=Easy_installer()#required to make class

    if sys.version_info >= (3, 9):
        easy.easy("zipfile39")
        import zipfile39 as zipfile
    elif sys.version_info >= (3, 8):
        easy.easy("zipfile38")
        import zipfile38 as zipfile
    elif sys.version_info >= (3, 7):
        easy.easy("zipfile37")
        import zipfile37 as zipfile
    elif sys.version_info >= (3, 6):
        easy.easy("zipfile36")
        import zipfile36 as zipfile
    else:
        easy.easy("zipfile")
        import zipfile
    




    #####################New Chrome Drivers###################    
    download_options=["chromedriver-linux64.zip","chromedriver-mac-x64.zip","chromedriver-mac-arm64.zip","chromedriver-win64.zip"]#"chromedriver-win32.zip"

    
    if version_num>114:
        x = requests.get('https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_STABLE')
        print(x.text)

        root_URL='''https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/'''
        possible_drivers=[]

        if "win" in platform.system().lower():
            download_option = [x for x in download_options if "win" in x]
            temp=root_URL+x.text+'''/'''+str(download_option[0]).replace("chromedriver-","").replace(".zip","")+'''/'''+str(download_option[0])
            print(temp)
            x = download_file(temp)
            with zipfile.ZipFile(temp.split('''/''')[-1],"r") as zip_ref:
                zip_ref.extractall(path=None, members=None, pwd=None)
                
        elif "linux" in platform.system().lower():
            download_option = [x for x in download_options if "linux" in x]
            temp=root_URL+x.text+'''/'''+str(download_option[0]).replace("chromedriver-","").replace(".zip","")+'''/'''+str(download_option[0])
            print(temp)
            x = download_file(temp)
            with zipfile.ZipFile(temp.split('''/''')[-1],"r") as zip_ref:
                zip_ref.extractall(path=None, members=None, pwd=None)
            
        elif "arm" in platform.system().lower():
            download_option = [x for x in download_options if "arm" in x]
            temp=root_URL+x.text+'''/'''+str(download_option[0]).replace("chromedriver-","").replace(".zip","")+'''/'''+str(download_option[0])
            print(temp)
            x = download_file(temp)
            with zipfile.ZipFile(temp.split('''/''')[-1],"r") as zip_ref:
                zip_ref.extractall(path=None, members=None, pwd=None)
                
        elif "mac" in platform.system().lower():
            download_option = [x for x in download_options if "mac" in x]
            temp=root_URL+x.text+'''/'''+str(download_option[0]).replace("chromedriver-","").replace(".zip","")+'''/'''+str(download_option[0])
            print(temp)
            x = download_file(temp)
            with zipfile.ZipFile(temp.split('''/''')[-1],"r") as zip_ref:
                zip_ref.extractall(path=None, members=None, pwd=None)

        else:
            for download_option in download_options:
                temp=root_URL+x.text+'''/'''+str(download_option[0]).replace("chromedriver-","").replace(".zip","")+'''/'''+str(download_option[0])
                print(temp)
                x = download_file(temp)
                with zipfile.ZipFile(temp.split('''/''')[-1],"r") as zip_ref:
                    zip_ref.extractall(path=None, members=None, pwd=None)
                    possible_drivers.append(zip_ref.namelist())


        extract_loc=str(download_option[0]).replace(".zip","")
        move_contents_up_one_level(extract_loc)

        #possible_drivers.append(zip_ref.namelist())
        #driver=[i for i in flatten(possible_drivers) if not "LICENSE" in i]
        #driver=driver[0]

        if _check():return webdriver.Chrome(driver)








    ####################Old Chrome Drivers######################
    download_options=["chromedriver_linux64.zip","chromedriver_mac64.zip","chromedriver_mac_arm64.zip","chromedriver_win32.zip"]

    
    if version_num<=114:
        x = requests.get('https://chromedriver.storage.googleapis.com/LATEST_RELEASE')
        #x = requests.get('https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_STABLE')
        print(x.text)

        possible_drivers=[]

        if "win" in platform.system().lower():
            download_option = [x for x in download_options if "win" in x]
            temp='https://chromedriver.storage.googleapis.com/'+x.text+'''/'''+str(download_option[0])
            print(temp)
            x = download_file(temp)
            with zipfile.ZipFile(temp.split('''/''')[-1],"r") as zip_ref:
                zip_ref.extractall(path=None, members=None, pwd=None)
                
        elif "linux" in platform.system().lower():
            download_option = [x for x in download_options if "linux" in x]
            temp='https://chromedriver.storage.googleapis.com/'+x.text+'''/'''+str(download_option[0])
            print(temp)
            x = download_file(temp)
            with zipfile.ZipFile(temp.split('''/''')[-1],"r") as zip_ref:
                zip_ref.extractall(path=None, members=None, pwd=None)
            
        elif "arm" in platform.system().lower():
            download_option = [x for x in download_options if "arm" in x]
            temp='https://chromedriver.storage.googleapis.com/'+x.text+'''/'''+str(download_option[0])
            print(temp)
            x = download_file(temp)
            with zipfile.ZipFile(temp.split('''/''')[-1],"r") as zip_ref:
                zip_ref.extractall(path=None, members=None, pwd=None)
                
        elif "mac" in platform.system().lower():
            download_option = [x for x in download_options if "mac" in x]
            temp='https://chromedriver.storage.googleapis.com/'+x.text+'''/'''+str(download_option[0])
            print(temp)
            x = download_file(temp)
            with zipfile.ZipFile(temp.split('''/''')[-1],"r") as zip_ref:
                zip_ref.extractall(path=None, members=None, pwd=None)

        else:
            for download_option in download_options:
                temp='https://chromedriver.storage.googleapis.com/'+x.text+'''/'''+str(download_option[0])
                print(temp)
                x = download_file(temp)
                with zipfile.ZipFile(temp.split('''/''')[-1],"r") as zip_ref:
                    zip_ref.extractall(path=None, members=None, pwd=None)
                    possible_drivers.append(zip_ref.namelist())
                    
                
        possible_drivers.append(zip_ref.namelist())
        driver=[i for i in flatten(possible_drivers) if not "LICENSE" in i]

        print(f"Attempting to locate driver pulling from: {driver}")
        driver=driver[0]
        if "linux" in platform.system().lower():driver=driver.replace(".exe","")
        return webdriver.Chrome(driver)

    print(f"Attempting to locate driver pulling from: {driver}")
    if "linux" in platform.system().lower():driver=driver.replace(".exe","")
    return webdriver.Chrome(driver)

    












