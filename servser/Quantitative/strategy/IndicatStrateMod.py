#! /usr/bin/env python 
#-*- encoding: utf-8 -*- 
#author pythontab.com 
import numpy as np
import pandas as pd
import pandas_datareader.data as web
import statsmodels.api as sm 
from statsmodels import regression
import datetime
import csv,os
import codecs
import talib
import copy
import json

class Excave_Indic_Base:
    def __init__(self):
        #挖掘衍生技术指标
        pass

    def plot_Aver_Cross(self, stock_df):
        #显示均线金叉/死叉提示符
        list_diff = np.sign(stock_df['Ma20']-stock_df['Ma60'])
        list_signal = np.sign(list_diff-list_diff.shift(1))
        #print "list_diff",list_diff   
        list_signal = list_signal[list_signal !=0]
        list_signal = list_signal.dropna(axis=0,how='any')#去除NA值
        #print "list_signal",list_signal
            
        dispCont_List = ["M20&M60 金叉:\n"+"日期:"+list_signal.index[x].strftime('%Y-%m-%d')+'\n' if list_signal[x] > 0 else "M20&M60 死叉:\n"+"日期:"+list_signal.index[x].strftime('%Y-%m-%d')+'\n' for x in range(0,len(list_signal.index))]#金叉时间
        
        return list_signal,dispCont_List
            
    def plot_Jump_Thrd(self, stock_df):     

        stock_df['changeRatio'] = stock_df.Close.pct_change()*100#计算涨/跌幅 (今收-昨收)/昨收*100% 判断向上跳空缺口/向下跳空缺口
        stock_df['preClose'] = stock_df.Close.shift(1) #增加昨收序列
        
        jump_threshold = stock_df.Close.median()*0.01 #跳空阈值 收盘价中位数*0.03
        #print "jump_threshold",jump_threshold
        jump_pd = pd.DataFrame()
        
        for kl_index in np.arange(0, stock_df.shape[0]):
            today = stock_df.ix[kl_index]
            """ 检测跳空缺口 """
            if (today.changeRatio > 0) and ((today.Low-today.preClose) > jump_threshold):
            #向上跳空 (今最低-昨收)/阈值
                today['jump_power'] = (today.Low-today.preClose)/jump_threshold
                jump_pd = jump_pd.append(today)

            elif (today.changeRatio < 0) and ((today.preClose-today.High) > jump_threshold):
            #向下跳空 (昨收-今最高)/阈值
                today['jump_power'] = (today.High-today.preClose)/jump_threshold
                jump_pd = jump_pd.append(today)
               
        jump_pd = jump_pd[(np.abs(jump_pd.changeRatio) > 2)&(jump_pd.Volume > 20000000)]#abs取绝对值
        
        dispCont_List = ["向上跳空:\n"+"日期:"+jump_pd.index[x].strftime('%Y-%m-%d')+'\n'+"缺口值:"+str('%.2f'%jump_pd.jump_power[x])+'\n' if jump_pd.jump_power[x] > 0 else "向下跳空:\n"+"日期:"+jump_pd.index[x].strftime('%Y-%m-%d')+'\n'+"缺口值:"+str('%.2f'%jump_pd.jump_power[x])+'\n' for x in range(0,len(jump_pd.index))]
        
        print (jump_pd.filter(['jump_power','preClose','changeRatio','Close','Volume']))#按顺序只显示该列        
        return jump_pd, dispCont_List


    def plot_Ndays_Break(self, stock_df):
        N1 = 42
        N2 = 30
        # stock_df['N1_High'] = pd.rolling_max(stock_df.High,window=N1)#计算最近N1个交易日最高价
        stock_df['N1_High'] = stock_df.High.rolling(window=N1).max()  #计算最近N1个交易日最高价
        stock_df['N1_High'] = stock_df['N1_High'].shift(1)
        # expan_max = pd.expanding_max(stock_df.Close)
        expan_max = stock_df.Close.expanding().max()
        stock_df['N1_High'].fillna(value=expan_max,inplace=True)#目前出现过的最大值填充前N1个nan

        # stock_df['N2_Low'] = pd.rolling_min(stock_df.Low,window=N2)#计算最近N2个交易日最低价   
        stock_df['N2_Low'] = stock_df.Low.rolling(window=N2).min()  # 计算最近N2个交易日最低价
        stock_df['N2_Low'] = stock_df['N2_Low'].shift(1) 
        # expan_min = pd.expanding_min(stock_df.Close)
        expan_min = stock_df.Close.expanding().min()
        stock_df['N2_Low'].fillna(value=expan_min,inplace=True)#目前出现过的最小值填充前N2个nan        
        
        dispCont_List = []
        break_pd = pd.DataFrame()
        
        for kl_index in np.arange(0, stock_df.shape[0]):
            today = stock_df.ix[kl_index]
            """ 收盘价超过N2最低价 卖出股票持有"""
            if today['Close'] < today['N2_Low']:
                break_pd = break_pd.append(today)
                dispCont_List.append("向下突破:"+stock_df.index[kl_index].strftime('%Y-%m-%d')+','+str(today['Close'])+'\n')#向下突破和价格
            """ 收盘价超过N1最高价 买入股票持有"""     
            if today['Close'] > today['N1_High']:
                break_pd = break_pd.append(today)
                dispCont_List.append("向上突破:"+stock_df.index[kl_index].strftime('%Y-%m-%d')+','+str(today['Close'])+'\n')#向上突破和价格
                          
        return break_pd, dispCont_List


class FactorBuyAverBreak:
    def __init__(self,**kwargs):
        self.xd = kwargs['xd']
    
    def make_buy_order(self):
        buy_signal = True
        return buy_signal
    
    def fit_day(self,kl_index, today, stock_df):
        day_ind = stock_df.index.get_loc(kl_index)

        if day_ind < self.xd - 1 or day_ind >= stock_df.shape[0] - 1:
            return False 

        if today.Close > stock_df.Close[day_ind-self.xd+1:day_ind+1].mean():
            print('FactorBuyAverBreak for info',kl_index,today.Close,stock_df.Close[day_ind-self.xd+1:day_ind+1].mean())
            return self.make_buy_order()
        return False
        
class FactorSellAverBreak:
    def __init__(self,**kwargs):
        self.xd = kwargs['xd']
        
    def fit_sell_order(self):
        sell_signal = True
        return sell_signal

    def fit_day(self,kl_index, today, stock_df):
        day_ind = stock_df.index.get_loc(kl_index)

        if day_ind < self.xd - 1 or day_ind >= stock_df.shape[0] - 1:
            return False 
       
        if today.Close < stock_df.Close[day_ind-self.xd+1:day_ind+1].mean():
            print('FactorSellAverBreak for info',kl_index,today.Close,stock_df.Close[day_ind-self.xd+1:day_ind+1].mean())
            #print 'FactorSellAverBreak for data',stock_df.Close[day_ind-self.xd+1:day_ind+1]
            return self.fit_sell_order()
        return False   
        
class FactorBuyNdayBreak:
    def __init__(self,**kwargs):
        self.xd = kwargs['xd']
    
    def make_buy_order(self):
        buy_signal = True
        return buy_signal
    
    def fit_day(self,kl_index, today, stock_df):
        day_ind = stock_df.index.get_loc(kl_index)

        if day_ind < self.xd - 1 or day_ind >= stock_df.shape[0] - 1:
            return False 
            
        if today.Close == stock_df.Close[day_ind-self.xd+1:day_ind+1].max():
            print('FactorBuyNdayBreak for info',kl_index,today.Close,stock_df.Close[day_ind-self.xd+1:day_ind+1].max())
            return self.make_buy_order()
        return False
        
class FactorSellNdayBreak:
    def __init__(self,**kwargs):
        self.xd = kwargs['xd']
        
    def fit_sell_order(self):
        sell_signal = True
        return sell_signal

    def fit_day(self,kl_index, today, stock_df):
        day_ind = stock_df.index.get_loc(kl_index)

        if day_ind < self.xd - 1 or day_ind >= stock_df.shape[0] - 1:
            return False 
       
        if today.Close == stock_df.Close[day_ind-self.xd+1:day_ind+1].min():
            print('FactorSellNdayBreak for info',kl_index,today.Close,stock_df.Close[day_ind-self.xd+1:day_ind+1].min())
            return self.fit_sell_order()
        return False  


class FactorSellAtrStop:
    def __init__(self,**kwargs):
        if 'stop_loss_n' in kwargs:
            #设置止损ATR倍数
            self.stop_loss_n = kwargs['stop_loss_n']
            
        if 'stop_win_n' in kwargs:
            #设置止盈ATR倍数
            self.stop_win_n = kwargs['stop_win_n']
                    
    def fit_sell_order(self):
        sell_signal = True
        return sell_signal

    def fit_day(self,kl_index, stock_df, Buy_Price):
        
        today = stock_df.ix[kl_index]#获取当天数据  
        
        if Buy_Price == 0:#无成交价格
            return False 
            
        if (Buy_Price > today.Close) and ((Buy_Price - today.Close) > self.stop_loss_n * today.atr14):
            print('stop_loss_n',kl_index,today.Close,Buy_Price)
            return self.fit_sell_order()
            
        elif (Buy_Price < today.Close) and ((today.Close - Buy_Price) > self.stop_win_n * today.atr14):            
            print('stop_win_n',kl_index,today.Close,Buy_Price)
            return self.fit_sell_order()
        else:
            return False

class QuantPickTimeSys:
    def __init__(self, kl_pd, buy_factors, sell_factors):
        # 回测阶段kl
        self.kl_pd = kl_pd
        
        # 初始化买入因子列表
        self.init_buy_factors(buy_factors)
        # 初始化卖出因子列表
        self.init_sell_factors(sell_factors)
        self.buy_price = 0#买入价格
        self.cash_hold = 100000#初始资金
        self.posit_num = 0#持股数目
        self.market_total = 0#持股市值 
        self.profit_curve = [] 

    def init_buy_factors(self, buy_factors):

        self.buy_factors = list()

        if buy_factors is None:
            return

        for factor_class in buy_factors:
            if factor_class is None:
                continue #执行下个循环
            if 'class' not in factor_class:
                raise ValueError('factor class key must name class!!')
            #print "before copy",id(factor_class)
            factor_class = copy.deepcopy(factor_class)
            #print "after copy",id(factor_class)
            class_fac = copy.deepcopy(factor_class['class'])
            del factor_class['class']
            #print "del",id(factor_class)
            
            '''实例化买入因子'''
            factor = class_fac(**factor_class)
            
            if not isinstance(factor, FactorBuyAverBreak) and not isinstance(factor, FactorBuyNdayBreak):#判断factor为基于FactorBuyBreak实例
                raise TypeError('factor must base FactorBuyBreak!!')
            self.buy_factors.append(factor)

    def init_sell_factors(self, sell_factors):
        """
        通过sell_factors实例化各个卖出因子
        :param sell_factors: list中元素为dict，每个dict为因子的构造元素，如class，构造参数等
        :return:
        """
        self.sell_factors = list()

        if sell_factors is None:
            return
        
        for factor_class in sell_factors:
            if factor_class is None:
                continue #执行下个循环
            if 'class' not in factor_class:
                raise ValueError('factor class key must name class!!')
            factor_class = copy.deepcopy(factor_class)
            class_fac = copy.deepcopy(factor_class['class'])
            del factor_class['class']
            
            '''实例化卖出因子'''
            factor = class_fac(**factor_class)
            
            if not isinstance(factor, FactorSellAverBreak) and not isinstance(factor, FactorSellNdayBreak):#判断factor为基于FactorBuyBreak实例
                raise TypeError('factor must base FactorSellBreak!!')
            self.sell_factors.append(factor)

            
    def _day_task(self, kl_index, today):
        fact_buy,fact_sell,sell_buf,buy_buf = 0,0,0,0
        for index, buy_factor in enumerate(self.buy_factors):
            #遍历所有买入因子
            buy_buf += buy_factor.fit_day(kl_index, today, self.kl_pd)
        fact_buy = 1 if (buy_buf == (index+1)) else 0
        for index, sell_factor in enumerate(self.sell_factors):
            #遍历所有卖出因子
            sell_buf += sell_factor.fit_day(kl_index, today, self.kl_pd)
        fact_sell = -1 if (sell_buf > 0) else 0
        return fact_buy or fact_sell
        
    # def run_factor_plot(self,subplotP0,subplotP1, subplotP2):
    def run_factor_plot(self):

        dispCont_List = []
        list_signal = []
        is_win = False
        self.kl_pd['Ma30'] = self.kl_pd.Close.rolling(window=30).mean()
        
        for kl_index,today in self.kl_pd.iterrows():

            signal = self._day_task(kl_index, today)
            
            if signal > 0:# 买入    
                if is_win == False:#空仓则买
                    start = self.kl_pd.index.get_loc(kl_index)
                    is_win = True
                   
                    self.posit_num = int(self.cash_hold/today.Close)
                    self.cash_hold = 0
                    dispCont_List_item = {
                        'type': 'start',
                        'order': self.kl_pd.index[start].strftime('%Y-%m-%d'),
                        'Close': today.Close
                    }
                    dispCont_List.append(dispCont_List_item)
                    
            elif signal < 0:# 卖出 
                if is_win == True:#避免未买先卖
                    end = self.kl_pd.index.get_loc(kl_index)
                    is_win = False
                    dispCont_List_item = {
                        'type': 'end',
                        'order': self.kl_pd.index[end].strftime('%Y-%m-%d'),
                        'Close': today.Close
                    }
                    dispCont_List.append(dispCont_List_item)

                    self.cash_hold = int(self.posit_num*today.Close)
                    self.market_total = 0
                    
            list_signal.append(is_win) 
            
            if is_win == True:
                self.market_total = int(self.posit_num*today.Close)
                self.profit_curve.append(self.market_total)
            else:
                self.profit_curve.append(self.cash_hold)

        self.kl_pd['keep'] = list_signal
        self.kl_pd['keep'].fillna(method = 'ffill',inplace = True)

        """ 计算基准收益 """
        self.kl_pd['benchmark_profit'] = np.log(self.kl_pd.Close/self.kl_pd.Close.shift(1))
        """ 计算趋势突破策略收益 """
        self.kl_pd['trend_profit'] = self.kl_pd.keep*self.kl_pd.benchmark_profit     
               
        self.kl_pd['profit'] = self.profit_curve
        factor_result = {
            'dispCont_List': dispCont_List,
            'benchmark_profit': json.loads(self.kl_pd['benchmark_profit'].to_json(orient="index")),
            'trend_profit': json.loads(self.kl_pd['trend_profit'].to_json(orient="index")),
            'profit': json.loads(self.kl_pd['profit'].to_json(orient="index"))
        }
        
        # return dispCont_List
        return factor_result

class FactorPickStockAng:  
    def __init__(self,**kwargs):            
        self.threshold_ang_min = -np.inf
        if 'threshold_ang_min' in kwargs:
            #设置最小角度阈值
            self.threshold_ang_min = kwargs['threshold_ang_min']
        self.threshold_ang_max = np.inf
        if 'threshold_ang_max' in kwargs:
            #设置最大角度阈值
            self.threshold_ang_max = kwargs['threshold_ang_max']
            
    def calc_regress_deg(self, y_arr):
        x= np.arange(0, len(y_arr))
        x = sm.add_constant(x)#添加常数列1
        
        model = regression.linear_model.OLS(y_arr, x).fit()#使用OLS做拟合
        rad = model.params[1]#y = kx + b :params[1] = k 
        deg = np.rad2deg(rad)#弧度转换为角度

        intercept = model.params[0]##y = kx + b :params[0] = b 
        reg_y_fit = x * rad + intercept
        
        return deg, x, reg_y_fit, y_arr  
            
    def fit_pick(self, Close):
        
        ang, x, reg_y_fit, y_arr = self.calc_regress_deg(Close)#计算走势角度
        return 'deg = '+str(ang) 
