#This is a file for easy imports and easy threading
#version 0.6

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
                print("MAX_PATH had and issue...")
        try:_=os.system("sudo apt -y install python3-pip")
        except:pass
        try:_=os.system("sudo apt -y install git")
        except:pass
        try:_=os.system("sudo apt -y install python3-dev ")
        except:pass
        
    
    
    def install_and_import(self,package):
        import warnings
        try:
            import importlib
            try:
                importlib.import_module(package)
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
                    main(['install',"--no-cache-dir", package])
                    
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
        if type(import_name)==type(None) and not type(easy_command)==type(None):
            self.install_and_import_special(url,command=easy_command)
        elif not type(import_name)==type(None) and type(easy_command)==type(None):
            self.install_and_import(url)
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
def generic_threader(function_name,datas,thread_count=16):
    
    #import zipfile
    import os
    from threading import Thread
    from  multiprocessing import Pipe
    #import shutil
    

    def target(conn,funtion_to_thread,tuple_of_data):
        conn.send(funtion_to_thread(tuple_of_data))
        
    total_processed=0     
    count=0
    current_working_threads=[]

    all_threads_datas=[]

    total_amount_of_data=len(datas)
    for data in datas:
        count+=1
        total_processed=+1
        
        parent_conn, child_conn =Pipe()
        
        t = Thread(target=target, args=(child_conn, function_name, data))
        t.start()
        
        current_working_threads.append((t,parent_conn,child_conn))    

        # limits Number of threads by forcing join every time thread count is a multible of thread_count
        if count%thread_count==0 or count>=total_amount_of_data:

            # collects all of the data to be return at the end
            for t,parent_conn,child_conn in current_working_threads:
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
    print("Total Processed: "+str(total_processed))
    return all_threads_datas
                
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
        return exchange_ids=ccxt.exchanges

    def help():
        temp="get_exchanges() returns list of exchanges get_simple returns data on symbols from exchanges symbols='' or [] exchange_ids='' or [] or None(default)"
        print(temp)
        return temp



