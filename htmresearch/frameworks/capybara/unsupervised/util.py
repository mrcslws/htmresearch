from collections import OrderedDict

import numpy as np
from matplotlib import colors
from matplotlib import pyplot as plt

from htmresearch.frameworks.capybara.unsupervised.cluster_distance import \
  percentOverlap, clusterDist



def convertNonZeroToSDR(patternNZs, numCells):
  sdrs = []
  for patternNZ in patternNZs:
    sdr = np.zeros(numCells)
    sdr[patternNZ] = 1
    sdrs.append(sdr)

  return sdrs



def computeDistanceMat(sdrs):
  """
  Compute distance matrix between SDRs
  :param sdrs: (array of arrays) array of SDRs
  :return: distance matrix
  """
  numSDRs = len(sdrs)
  # calculate pairwise distance
  distanceMat = np.zeros((numSDRs, numSDRs), dtype=np.float64)
  for i in range(numSDRs):
    for j in range(numSDRs):
      distanceMat[i, j] = 1 - percentOverlap(sdrs[i], sdrs[j])
  return distanceMat



def computeClusterDistanceMat(sdrClusters, numCells):
  """
  Compute distance matrix between clusters of SDRs
  :param sdrClusters: list of sdr clusters,
                      each cluster is a list of SDRs
                      each SDR is a list of active indices
  :return: distance matrix
  """
  numClusters = len(sdrClusters)
  distanceMat = np.zeros((numClusters, numClusters), dtype=np.float64)
  for i in range(numClusters):
    for j in range(i, numClusters):
      distanceMat[i, j] = clusterDist(sdrClusters[i], sdrClusters[j], numCells)
      distanceMat[j, i] = distanceMat[i, j]

  return distanceMat



def viz2DProjection(vizTitle, outputFile, numClusters, clusterAssignments,
                    npos):
  """
  Visualize SDR clusters with MDS
  """

  colorList = colors.cnames.keys()
  plt.figure()
  colorList = colorList
  colorNames = []
  for i in range(len(clusterAssignments)):
    clusterId = int(clusterAssignments[i])
    if clusterId not in colorNames:
      colorNames.append(clusterId)
    sdrProjection = npos[i]
    label = 'Category %s' % clusterId
    if len(colorList) > clusterId:
      color = colorList[clusterId]
    else:
      color = 'black'
    plt.scatter(sdrProjection[0], sdrProjection[1], label=label, alpha=0.5,
                color=color, marker='o', edgecolor='black')

  # Add nicely formatted legend
  handles, labels = plt.gca().get_legend_handles_labels()
  by_label = OrderedDict(zip(labels, handles))
  plt.legend(by_label.values(), by_label.keys(), scatterpoints=1, loc=2)

  plt.title(vizTitle)
  plt.draw()
  plt.savefig(outputFile)



def assignClusters(sdrs, numClusters, numSDRsPerCluster):
  clusterAssignments = np.zeros(len(sdrs))

  clusterIDs = range(numClusters)
  for clusterID in clusterIDs:
    selectPts = np.arange(numSDRsPerCluster) + clusterID * numSDRsPerCluster
    clusterAssignments[selectPts] = clusterID

  return clusterAssignments


def plotDistanceMat(distanceMat, title, outputFile, showPlot=False):
  plt.figure()
  plt.imshow(distanceMat, interpolation="nearest")
  plt.colorbar()
  plt.title(title)
  plt.savefig(outputFile)
  plt.draw()
  if showPlot:
    plt.show()
