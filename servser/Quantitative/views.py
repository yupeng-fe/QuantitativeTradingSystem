
from django.shortcuts import render
from django.http import HttpResponse
import json
import datetime
from . import controller

# Create your views here.
def index(request):
    return HttpResponse('hello world')

# 用户信息
# login
def login(request):
    return HttpResponse(json.dumps(controller.User.login(request)), content_type="application/json")
# register
def register(request):
    return HttpResponse(json.dumps(controller.User.register(request)), content_type="application/json")
# Loginout
def loginout(request):
    return HttpResponse(json.dumps(controller.User.loginout(request)), content_type="application/json")
# User
def setUserInfo(request):
    return HttpResponse(json.dumps(controller.User.setUserInfo(request)), content_type="application/json")
# change password
def changePassword(request):
    return HttpResponse(json.dumps(controller.User.changePassword(request)), content_type="application/json")


# 获取Stock数据
def getStockData(request):
    return HttpResponse(json.dumps(controller.Stock.getStockData(request)), content_type="application/json")
# 获取上市公司信息
def getStockCompany(request):
    return HttpResponse(json.dumps(controller.Stock.getStockCompany(request)), content_type="application/json")
def getStockCompanyDetail(request):
    return HttpResponse(json.dumps(controller.Stock.getStockCompanyDetail(request)), content_type="application/json")
# 搜索公司信息
def searchStockCompany(request):
    return HttpResponse(json.dumps(controller.Stock.searchStockCompany(request)), content_type="application/json")
# 收藏公司
def collectionCompany(request):
    return HttpResponse(json.dumps(controller.CompanyCollection.collectionCompany(request)), content_type="application/json")
# 查询用户是否收藏该公司
def isCompanyCollection(request):
    return HttpResponse(json.dumps(controller.CompanyCollection.isCompanyCollection(request)), content_type="application/json")
def cancelCollectionCompany(request):
    return HttpResponse(json.dumps(controller.CompanyCollection.cancelCollectionCompany(request)), content_type="application/json")
def getUserCollectCompany(request):
    return HttpResponse(json.dumps(controller.CompanyCollection.getUserCollectCompany(request)), content_type="application/json")
# 存储股票数据测试
def stockDataTest(request):
    return HttpResponse(json.dumps(controller.Stock.stockDataTest(request)), content_type="application/json")

# 回测
def runStrategy(request):
    return HttpResponse(json.dumps(controller.RunStrategy.runStrategy(request)), content_type="application/json")


def loopBack(request):
    runLoopBack = controller.RunLoopBack.RunLoopBack(request)
    return HttpResponse(json.dumps(runLoopBack.runLoopBack(request)), content_type="application/json")

def strategyTrade(request):
    # resp = controller.Stock.exampleTrade(request);
    resp = controller.Stock.strategyTrade(request);

    return HttpResponse(json.dumps(resp), content_type="application/json")
def test(request):
    print('enter test request')
    return HttpResponse(json.dumps({"1": "1"}), content_type="application/json")
