import requests
import os
import time
import ctypes
import datetime
import threading
import configparser
from bs4 import BeautifulSoup as bs
#import balloontip as bt

# 소스위치
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

#config 파일 load
config = configparser.ConfigParser()
config.sections()
config.read(os.path.join(BASE_DIR, 'config.ini'))

F_LOGIN_ID = config['LOGIN']['LOGIN_ID']
F_LOGIN_PW = config['LOGIN']['LOGIN_PW']
F_FILTER_URL = config['URL']['FILTER_URL']
F_REFRESH_TIME = config['TIME']['REFRESH_TIME']

# 로그인할 유저정보
LOGIN_INFO = {
	'os_username': F_LOGIN_ID,
	'os_password': F_LOGIN_PW,
	'os_destination': '',
	'user_role': '',
	'atl_token': ''
}
#JQL로 쿼리작성 후 해당 링크 사용(filterID)
FILTER_URL = F_FILTER_URL
#새로고침 주기(분)
REFRESH_TIME = int(F_REFRESH_TIME)

def showMegBox(msg):
	ctypes.windll.user32.MessageBoxW(0, msg, "Mcols알림", 0)

# Session 생성, with 구문 안에서 유지
with requests.Session() as s:
	
	#로그인 
	login_req = s.post('https://mcols.hyundai-mnsoft.com:8443/login.jsp', data=LOGIN_INFO)
	if login_req.status_code != 200:
		raise Exception(login_req.status_code + ' - 페이지 로딩 실패')
	else:
		soup = bs(login_req.text, 'html.parser')
		loginFailStr = soup.select('#login-form > div.form-body > div.aui-message.error > p')
		if len(loginFailStr) > 0:
			raise Exception('로그인 실패. 아이디와 비번 확인 세요!')
		else:
			print("로그인 성공")

	while True:
		post_one = s.get(FILTER_URL)
		soup = bs(post_one.text, 'html.parser')
		mcolsList = soup.select('#issuetable td.issuekey a')
		
		newList = []
		sameFlg = False
		
		if len(mcolsList) > 0:
			now = datetime.datetime.now()
			nowDatetime = now.strftime('%Y-%m-%d %H:%M:%S')
			
			#이전리스트 저장파일 읽기
			with open(os.path.join(BASE_DIR, 'latest.txt'), 'r') as f_read:
				fileList = f_read.read().splitlines()
				f_read.close()
			
			#Mocls와 파일 비교
			for i in range(0, len(mcolsList)):
				if len(fileList) > 0:
					for j in range(0, len(fileList)):
						sameFlg = False
						if mcolsList[i].text == fileList[j]:
							sameFlg = True
							break
				if sameFlg == False: 
					newList.append(mcolsList[i].text)

			#메세지 출력
			if len(newList) != 0:
				popMsgStr = "[ " + nowDatetime + " ] 새로운 이슈가 등록되었습니다.\n"
				for i in range(0, len(newList)):
					popMsgStr += newList[i] + '\n'
				print(popMsgStr)
				t1 = threading.Thread(target=showMegBox, args=(popMsgStr,))
				t1.daemon = True
				t1.start()
				#bt.balloon_tip(popMsgTitle, popMsgStr)
			else:
				print('[ ' + nowDatetime + ' ] 새 글이 없습니다.!')					

			#현재리스트 파일 저장
			with open(os.path.join(BASE_DIR, 'latest.txt'), 'w') as f_write:
				for i in range(0, len(mcolsList)):
					f_write.write(mcolsList[i].text+"\n")
				f_write.close()

		time.sleep(REFRESH_TIME*60)