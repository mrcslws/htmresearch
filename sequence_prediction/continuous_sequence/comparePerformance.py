# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013-2015, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------
import csv, sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
from optparse import OptionParser
from swarm_runner import SwarmRunner
from nrmse import *
rcParams.update({'figure.autolayout': True})
plt.ion()
plt.close('all')


def loadTrueDataFile(filePath):
  data = pd.read_csv(filePath, header=0, nrows=1)
  colnames = data.columns.values
  ncol = len(colnames)

  # data = pd.read_csv(filePath, header=0, skiprows=[1,2], names=['step', 'value', 'prediction'])

  if ncol == 2:
    data = pd.read_csv(filePath, header=0, skiprows=[1,2], names=['step', 'value'])
  elif ncol == 3:
    data = pd.read_csv(filePath, header=0, skiprows=[1,2], names=['step', 'value', 'prediction'])
  elif ncol == 4:
    data = pd.read_csv(filePath, header=0, skiprows=[1,2], names=['step', 'value', 'timeofday', 'dayofweek'])
  return data



def loadDataFileLSTM(filePath):
  data = pd.read_csv(filePath, header=0, nrows=1)
  colnames = data.columns.values
  ncol = len(colnames)
  data = pd.read_csv(filePath, header=0, skiprows=[1,2], names=['step', 'value', 'prediction5'])

  return data


def loadDataFile(filePath):
  data = pd.read_csv(filePath, header=0, nrows=1)
  colnames = data.columns.values
  ncol = len(colnames)

  # data = pd.read_csv(filePath, header=0, skiprows=[1,2], names=['step', 'value', 'prediction'])

  if ncol == 2:
    data = pd.read_csv(filePath, header=0, skiprows=[1,2], names=['step', 'value'])
  elif ncol == 3:
    data = pd.read_csv(filePath, header=0, skiprows=[1,2], names=['step', 'value', 'prediction'])
  elif ncol == 4:
    data = pd.read_csv(filePath, header=0, skiprows=[1,2], names=['step', 'data', 'prediction1', 'prediction5'])
  return data


def plotPerformance(dataSet, nTrain):
  # filePath = './data/' + dataSet + '.csv'
  # print "load test data from ", filePath
  # trueData = loadDataFile(filePath)
  # trueData = trueData['value']
  #
  # filePath = './prediction/' + dataSet + '_TM_pred.csv'
  # print "load TM prediction from ", filePath
  # predData_TM = loadDataFile(filePath)
  #
  # filePath = './prediction/' + dataSet + '_ARIMA_pred.csv'
  # predData_ARIMA = loadDataFile(filePath)
  #
  # print "nTrain: ", nTrain
  # print "nTest: ", len(trueData[nTrain:])
  #
  # # trivial shift predictor
  # predData_shift = np.roll(trueData, 1)
  # predData_TM_one_step = np.roll(predData_TM['prediction1'], 1)
  # predData_ARIMA_one_step = np.roll(predData_ARIMA['prediction1'], 1)
  #
  # trueData = trueData[nTrain:]
  # predData_TM_one_step = predData_TM_one_step[nTrain:]
  # predData_shift = predData_shift[nTrain:]
  # predData_ARIMA_one_step = predData_ARIMA_one_step[nTrain:]
  #
  # NRMSE_TM = NRMSE(trueData, predData_TM_one_step)
  # NRMSE_ARIMA = NRMSE(trueData, predData_ARIMA_one_step)
  # NRMSE_Shift = NRMSE(trueData, predData_shift)
  #
  # print "NRMSE: Shift - 1step", NRMSE_Shift
  # print "NRMSE: TM - 1 step", NRMSE_TM
  # print "NRMSE: ARIMA - 1 step", NRMSE_ARIMA
  #
  # plt.figure(1)
  # plt.plot(trueData, label='True Data', color='black')
  # plt.plot(predData_shift, label='Trival NRMSE: '+"%0.3f" % NRMSE_Shift)
  # plt.plot(predData_ARIMA_one_step, label='ARIMA NRMSE: '+"%0.3f" % NRMSE_ARIMA)
  # plt.plot(predData_TM_one_step, label='TM, NRMSE: '+"%0.3f" % NRMSE_TM)
  # plt.legend()
  # plt.xlabel('Time')
  # fileName = './result/'+dataSet+"modelPrediction.pdf"
  # print "save example prediction trace to ", fileName
  # plt.savefig(fileName)

  # resTM = abs(trueData-predData_TM)
  # res_shift = abs(trueData-predData_shift)
  # resTM = resTM[np.isnan(resTM) == False]
  # res_shift = res_shift[np.isnan(res_shift) == False]
  # plt.figure(2)
  # xl = [0, max(max(resTM), max(res_shift))]
  # plt.subplot(2,2,1)
  # plt.hist(resTM)
  # plt.title('TM median='+"%0.3f" % np.median(resTM)+' NRMSE: '+"%0.3f" % NRMSE_TM)
  # plt.xlim(xl)
  # plt.xlabel("|residual|")
  # plt.subplot(2,2,3)
  # plt.hist(res_shift)
  # plt.title('Trivial median='+"%0.3f" % np.median(res_shift)+' NRMSE: '+"%0.3f" % NRMSE_Shift)
  # plt.xlim(xl)
  # plt.xlabel("|residual|")
  # fileName = './result/'+dataSet+"error_distribution.pdf"
  # print "save residual error distribution to ", fileName
  # plt.savefig(fileName)


  filePath = './data/' + dataSet + '.csv'
  print "load test data from ", filePath
  trueData = loadTrueDataFile(filePath)
  trueData = trueData['value'].astype('float')

  filePath = './prediction/' + dataSet + '_TM_pred.csv'
  print "load TM prediction from ", filePath
  predData_TM = loadDataFileLSTM(filePath)

  filePath = './prediction/' + dataSet + '_ARIMA_pred.csv'
  predData_ARIMA = loadDataFile(filePath)

  filePath = './prediction/' + dataSet + '_lstm_pred.csv'
  predData_LSTM = loadDataFileLSTM(filePath)


  nTest = len(trueData) - nTrain - 5
  print "nTrain: ", nTrain
  print "nTest: ", len(trueData[nTrain:])

  # trivial shift predictor
  predData_shift = np.roll(trueData, 5)
  predData_TM_five_step = np.roll(predData_TM['prediction5'], 5)
  predData_ARIMA_five_step = predData_shift
  # predData_ARIMA_five_step = np.roll(predData_ARIMA['prediction5'], 5)
  predData_LSTM_five_step = np.roll(predData_LSTM['prediction5'], 5)

  time_step = predData_TM['step']

  nrmse_window = 1000
  (window_center, nrmse_slide_tm) = NRMSE_sliding(trueData, predData_TM_five_step, nrmse_window)
  (window_center, nrmse_slide_lstm) = NRMSE_sliding(trueData, predData_LSTM_five_step, nrmse_window)
  (window_center, nrmse_slide_shift) = NRMSE_sliding(trueData, predData_shift, nrmse_window)

  plt.figure(1)
  plt.plot(window_center, nrmse_slide_tm, label='TM')
  plt.plot(window_center, nrmse_slide_lstm, label='LSTM')
  plt.plot(window_center, nrmse_slide_shift, label='Shift')
  plt.legend()

  trueData = trueData[nTrain:nTrain+nTest]
  predData_TM_five_step = predData_TM_five_step[nTrain:nTrain+nTest]
  predData_shift = predData_shift[nTrain:nTrain+nTest]
  predData_ARIMA_five_step = predData_ARIMA_five_step[nTrain:nTrain+nTest]
  predData_LSTM_five_step = predData_LSTM_five_step[nTrain:nTrain+nTest]
  time_step = time_step[nTrain:nTrain+nTest]

  NRMSE_TM = NRMSE(trueData, predData_TM_five_step)
  NRMSE_ARIMA = NRMSE(trueData, predData_ARIMA_five_step)
  NRMSE_LSTM = NRMSE(trueData, predData_LSTM_five_step)
  NRMSE_Shift = NRMSE(trueData, predData_shift)



  print "NRMSE: Shift - 5 step", NRMSE_Shift
  print "NRMSE: TM - 5 step", NRMSE_TM
  print "NRMSE: ARIMA - 5 step", NRMSE_ARIMA
  print "NRMSE: LSTM - 5 step", NRMSE_LSTM

  time_step = pd.to_datetime(time_step)
  plt.figure(2)
  plt.plot(time_step, trueData, label='True Data', color='black')
  # plt.plot(time_step, predData_shift, label='Trival NRMSE: '+"%0.3f" % NRMSE_Shift)
  # plt.plot(time_step, predData_ARIMA_five_step, label='ARIMA NRMSE: '+"%0.3f" % NRMSE_ARIMA)
  plt.plot(time_step, predData_TM_five_step, label='TM, NRMSE: '+"%0.3f" % NRMSE_TM)
  plt.plot(time_step, predData_LSTM_five_step, label='LSTM, NRMSE: '+"%0.3f" % NRMSE_LSTM)
  plt.legend()
  plt.xlabel('Time')
  plt.ylabel('Passenger Count')
  plt.xlim([time_step.values[0], time_step.values[400]])
  fileName = './result/'+dataSet+"modelPrediction.pdf"
  print "save example prediction trace to ", fileName
  plt.savefig(fileName)

  fig, ax = plt.subplots()
  inds = np.arange(4)
  ax.bar(inds, [NRMSE_Shift, NRMSE_LSTM, NRMSE_ARIMA, NRMSE_TM], width=0.3)
  ax.set_xticks(inds+0.3/2)
  ax.set_xticklabels( ('Shift', 'LSTM', 'ARIMA', 'TM') )
  ax.set_ylabel('NRMSE')

  # import plotly.plotly as py
  # plot_url = py.plot_mpl(fig)


def _getArgs():
  parser = OptionParser(usage="%prog PARAMS_DIR OUTPUT_DIR [options]"
                              "\n\nCompare TM performance with trivial predictor using "
                              "model outputs in prediction directory "
                              "and outputting results to result directory.")
  parser.add_option("-d",
                    "--dataSet",
                    type=str,
                    default=0,
                    dest="dataSet",
                    help="DataSet Name, choose from sine, SantaFe_A, MackeyGlass")
  (options, args) = parser.parse_args(sys.argv[1:])

  return options, args


if __name__ == "__main__":

  (_options, _args) = _getArgs()
  dataSet = _options.dataSet
  SWARM_CONFIG = SwarmRunner.importSwarmDescription(dataSet)
  nTrain = SWARM_CONFIG["streamDef"]['streams'][0]['last_record']
  print 'Compare Model performance for ', dataSet
  plotPerformance(dataSet, nTrain)
