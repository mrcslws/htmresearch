# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2016, Numenta, Inc.  Unless you have an agreement
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

"""
This file plots the convergence of L4-L2 as you increase the number of columns,
or adjust the confusion between objects.

"""

import random
import os
from math import ceil
import pprint
import numpy
import cPickle
from multiprocessing import Pool
import matplotlib.pyplot as plt
import matplotlib as mpl
mpl.rcParams['pdf.fonttype'] = 42

from htmresearch.frameworks.layers.l2_l4_inference import L4L2Experiment
from htmresearch.frameworks.layers.object_machine_factory import (
  createObjectMachine
)

def locateConvergencePoint(stats, minOverlap, maxOverlap):
  """
  Walk backwards through stats until you locate the first point that diverges
  from target overlap values.  We need this to handle cases where it might get
  to target values, diverge, and then get back again.  We want the last
  convergence point.
  """
  for i,v in enumerate(stats[::-1]):
    if not (v >= minOverlap and v <= maxOverlap):
      return len(stats)-i + 1

  # Never differs - converged in one iteration
  return 1


def averageConvergencePoint(inferenceStats, prefix, minOverlap, maxOverlap,
                            settlingTime):
  """
  inferenceStats contains activity traces while the system visits each object.

  Given the i'th object, inferenceStats[i] contains activity statistics for
  each column for each region for the entire sequence of sensations.

  For each object, compute the convergence time - the first point when all
  L2 columns have converged.

  Return the average convergence time across all objects.

  Given inference statistics for a bunch of runs, locate all traces with the
  given prefix. For each trace locate the iteration where it finally settles
  on targetValue. Return the average settling iteration across all runs.
  """
  convergenceSum = 0.0

  # For each object
  for stats in inferenceStats:

    # For each L2 column locate convergence time
    convergencePoint = 0.0
    for key in stats.iterkeys():
      if prefix in key:
        columnConvergence = locateConvergencePoint(
          stats[key], minOverlap, maxOverlap)

        # Ensure this column has converged by the last iteration
        # assert(columnConvergence <= len(stats[key]))

        convergencePoint = max(convergencePoint, columnConvergence)

    convergenceSum += ceil(float(convergencePoint)/settlingTime)

  return convergenceSum/len(inferenceStats)


def objectConfusion(objects):
  """
  For debugging, print overlap between each pair of objects.
  """
  sumCommonLocations = 0
  sumCommonFeatures = 0
  sumCommonPairs = 0
  numObjects = 0
  commonPairHistogram = numpy.zeros(len(objects[0]), dtype=numpy.int32)
  for o1,s1 in objects.iteritems():
    for o2,s2 in objects.iteritems():
      if o1 != o2:
        # Count number of common locations id's and common feature id's
        commonLocations = 0
        commonFeatures = 0
        for pair1 in s1:
          for pair2 in s2:
            if pair1[0] == pair2[0]: commonLocations += 1
            if pair1[1] == pair2[1]: commonFeatures += 1

        # print "Confusion",o1,o2,", common pairs=",len(set(s1)&set(s2)),
        # print ", common locations=",commonLocations,"common features=",commonFeatures

        assert(len(set(s1)&set(s2)) != len(s1) ), "Two objects are identical!"

        sumCommonPairs += len(set(s1)&set(s2))
        sumCommonLocations += commonLocations
        sumCommonFeatures += commonFeatures
        commonPairHistogram[len(set(s1)&set(s2))] += 1
        numObjects += 1

  print "Average common pairs=", sumCommonPairs / float(numObjects),
  print ", locations=",sumCommonLocations / float(numObjects),
  print ", features=",sumCommonFeatures / float(numObjects)
  print "Common pair histogram=",commonPairHistogram


def runExperiment(args):
  """
  Run experiment.  What did you think this does?

  args is a dict representing the parameters. We do it this way to support
  multiprocessing. args contains one or more of the following keys:

  @param noiseLevel  (float) Noise level to add to the locations and features
                             during inference. Default: None
  @param numObjects  (int)   The number of objects we will train.
                             Default: 10
  @param numPoints   (int)   The number of points on each object.
                             Default: 10
  @param pointRange  (int)   Creates objects each with points ranging from
                             [numPoints,...,numPoints+pointRange-1]
                             A total of numObjects * pointRange objects will be
                             created.
                             Default: 1
  @param numLocations (int)  For each point, the number of locations to choose
                             from.  Default: 10
  @param numFeatures (int)   For each point, the number of features to choose
                             from.  Default: 10
  @param numColumns  (int)   The total number of cortical columns in network.
                             Default: 2
  @param settlingTime (int)  Number of iterations we wait to let columns
                             stabilize. Important for multicolumn experiments
                             with lateral connections.

  @param includeRandomLocation (bool) If True, a random location SDR will be
                             generated during inference for each feature.

  The method returns the args dict updated with two additional keys:
    convergencePoint (int)   The average number of iterations it took
                             to converge across all objects
    objects          (pairs) The list of objects we trained on
  """
  numObjects = args.get("numObjects", 10)
  numLocations = args.get("numLocations", 10)
  numFeatures = args.get("numFeatures", 10)
  numColumns = args.get("numColumns", 2)
  noiseLevel = args.get("noiseLevel", None)  # TODO: implement this?
  numPoints = args.get("numPoints", 10)
  trialNum = args.get("trialNum", 42)
  pointRange = args.get("pointRange", 1)
  plotInferenceStats = args.get("plotInferenceStats", True)
  settlingTime = args.get("settlingTime", 3)
  includeRandomLocation = args.get("includeRandomLocation", False)

  # Create the objects
  objects = createObjectMachine(
    machineType="simple",
    numInputBits=20,
    sensorInputSize=150,
    externalInputSize=2400,
    numCorticalColumns=numColumns,
    numFeatures=numFeatures,
    seed=trialNum
  )

  for p in range(pointRange):
    objects.createRandomObjects(numObjects, numPoints=numPoints+p,
                                      numLocations=numLocations,
                                      numFeatures=numFeatures)

  objectConfusion(objects.getObjects())

  # print "Total number of objects created:",len(objects.getObjects())
  # print "Objects are:"
  # for o in objects:
  #   pairs = objects[o]
  #   pairs.sort()
  #   print str(o) + ": " + str(pairs)

  # Setup experiment and train the network
  name = "convergence_O%03d_L%03d_F%03d_C%03d_T%03d" % (
    numObjects, numLocations, numFeatures, numColumns, trialNum
  )
  exp = L4L2Experiment(
    name,
    numCorticalColumns=numColumns,
    inputSize=150,
    externalInputSize=2400,
    numInputBits=20,
    seed=trialNum
  )

  exp.learnObjects(objects.provideObjectsToLearn())

  # For inference, we will check and plot convergence for each object. For each
  # object, we create a sequence of random sensations for each column.  We will
  # present each sensation for settlingTime time steps to let it settle and
  # ensure it converges.
  for objectId in objects:
    obj = objects[objectId]

    objectSensations = {}
    for c in range(numColumns):
      objectSensations[c] = []

    if numColumns > 1:
      # Create sequence of random sensations for this object for all columns At
      # any point in time, ensure each column touches a unique loc,feature pair
      # on the object.  It is ok for a given column to sense a loc,feature pair
      # more than once. The total number of sensations is equal to the number of
      # points on the object.
      for sensationNumber in range(len(obj)):
        # Randomly shuffle points for each sensation
        objectCopy = [pair for pair in obj]
        random.shuffle(objectCopy)
        for c in range(numColumns):
          # stay multiple steps on each sensation
          for _ in xrange(settlingTime):
            objectSensations[c].append(objectCopy[c])

    else:
      # Create sequence of sensations for this object for one column. The total
      # number of sensations is equal to the number of points on the object. No
      # point should be visited more than once.
      objectCopy = [pair for pair in obj]
      random.shuffle(objectCopy)
      for pair in objectCopy:
        # stay multiple steps on each sensation
        for _ in xrange(settlingTime):
          objectSensations[0].append(pair)

    inferConfig = {
      "object": objectId,
      "numSteps": len(objectSensations[0]),
      "pairs": objectSensations,
      "includeRandomLocation": includeRandomLocation,
    }

    inferenceSDRs = objects.provideObjectToInfer(inferConfig)

    exp.infer(inferenceSDRs, objectName=objectId)

    if plotInferenceStats:
      exp.plotInferenceStats(
        fields=["L2 Representation",
                "Overlap L2 with object",
                "L4 Representation"],
        experimentID=objectId,
        onePlot=False,
      )

  convergencePoint = averageConvergencePoint(
    exp.getInferenceStats(),"L2 Representation", 30, 40, settlingTime)

  print
  print "# objects {} # features {} # locations {} # columns {} trial # {}".format(
    numObjects, numFeatures, numLocations, numColumns, trialNum)
  print "Average convergence point=",convergencePoint

  # Return our convergence point as well as all the parameters and objects
  args.update({"objects": objects.getObjects()})
  args.update({"convergencePoint":convergencePoint})

  # Can't pickle experiment so can't return it for batch multiprocessing runs.
  # However this is very useful for debugging when running in a single thread.
  if plotInferenceStats:
    args.update({"experiment": exp})
  return args


def runExperimentPool(numObjects,
                      numLocations,
                      numFeatures,
                      numColumns,
                      numWorkers=7,
                      nTrials=1,
                      pointRange=1,
                      numPoints=10,
                      includeRandomLocation=False,
                      resultsName="convergence_results.pkl"):
  """
  Allows you to run a number of experiments using multiple processes.
  For each parameter except numWorkers, pass in a list containing valid values
  for that parameter. The cross product of everything is run, and each
  combination is run nTrials times.

  Returns a list of dict containing detailed results from each experiment.
  Also pickles and saves the results in resultsName for later analysis.

  Example:
    results = runExperimentPool(
                          numObjects=[10],
                          numLocations=[5],
                          numFeatures=[5],
                          numColumns=[2,3,4,5,6],
                          numWorkers=8,
                          nTrials=5)
  """
  # Create function arguments for every possibility
  args = []
  for t in range(nTrials):
    for c in numColumns:
      for o in numObjects:
        for l in numLocations:
          for f in numFeatures:
            args.append(
              {"numObjects": o,
               "numLocations": l,
               "numFeatures": f,
               "numColumns": c,
               "trialNum": t,
               "pointRange": pointRange,
               "numPoints": numPoints,
               "plotInferenceStats": False,
               "includeRandomLocation": includeRandomLocation,
               "settlingTime": 3,
               }
            )

  print "{} experiments to run, {} workers".format(len(args), numWorkers)
  # Run the pool
  if numWorkers > 1:
    pool = Pool(processes=numWorkers)
    result = pool.map(runExperiment, args)
  else:
    result = []
    for arg in args:
      result.append(runExperiment(arg))

  # print "Full results:"
  # pprint.pprint(result, width=150)

  # Pickle results for later use
  with open(resultsName,"wb") as f:
    cPickle.dump(result,f)

  return result


def plotConvergenceByColumn(results, columnRange, featureRange, numTrials):
  """
  Plots the convergence graph: iterations vs number of columns.
  Each curve shows the convergence for a given number of unique features.
  """
  ########################################################################
  #
  # Accumulate all the results per column in a convergence array.
  #
  # Convergence[f,c] = how long it took it to  converge with f unique features
  # and c columns.

  convergence = numpy.zeros((max(featureRange), max(columnRange) + 1))
  for r in results:
    convergence[r["numFeatures"] - 1,
                r["numColumns"]] += r["convergencePoint"]

  convergence /= numTrials

  # For each column, print convergence as fct of number of unique features
  for c in range(1, max(columnRange) + 1):
    print c, convergence[:, c]

  # Print everything anyway for debugging
  print "Average convergence array=", convergence

  ########################################################################
  #
  # Create the plot. x-axis=
  plt.figure()
  plotPath = os.path.join("plots", "convergence_by_column.pdf")

  # Plot each curve
  legendList = []
  colorList = ['r', 'b', 'g', 'm', 'c', 'k', 'y']

  for i in range(len(featureRange)):
    f = featureRange[i]
    print columnRange
    print convergence[f-1,columnRange]
    legendList.append('Unique features={}'.format(f))
    plt.plot(columnRange, convergence[f-1,columnRange],
             color=colorList[i])

  # format
  plt.legend(legendList, loc="upper right")
  plt.xlabel("Number of columns")
  plt.xticks(columnRange)
  plt.yticks(range(0,int(convergence.max())+1))
  plt.ylabel("Average number of touches")
  plt.title("Number of touches to recognize one object (multiple columns)")

    # save
  plt.savefig(plotPath)
  plt.close()


def plotConvergenceByObject(results, objectRange, featureRange):
  """
  Plots the convergence graph: iterations vs number of objects.
  Each curve shows the convergence for a given number of unique features.
  """
  ########################################################################
  #
  # Accumulate all the results per column in a convergence array.
  #
  # Convergence[f,o] = how long it took it to converge with f unique features
  # and o objects.

  convergence = numpy.zeros((max(featureRange), max(objectRange) + 1))
  for r in results:
    if r["numFeatures"] in featureRange:
      convergence[r["numFeatures"] - 1, r["numObjects"]] += r["convergencePoint"]

  convergence /= numTrials

  ########################################################################
  #
  # Create the plot. x-axis=
  plt.figure()
  plotPath = os.path.join("plots", "convergence_by_object_random_location.pdf")

  # Plot each curve
  legendList = []
  colorList = ['r', 'b', 'g', 'm', 'c', 'k', 'y']

  for i in range(len(featureRange)):
    f = featureRange[i]
    print "features={} objectRange={} convergence={}".format(
      f,objectRange, convergence[f-1,objectRange])
    legendList.append('Unique features={}'.format(f))
    plt.plot(objectRange, convergence[f-1,objectRange],
             color=colorList[i])

  # format
  plt.legend(legendList, loc="lower right", prop={'size':10})
  plt.xlabel("Number of objects in training set")
  plt.xticks(range(0,max(objectRange)+1,10))
  plt.yticks(range(0,int(convergence.max())+2))
  plt.ylabel("Average number of touches")
  plt.title("Number of touches to recognize one object (single column)")

    # save
  plt.savefig(plotPath)
  plt.close()


def plotConvergenceByObjectMultiColumn(results, objectRange, columnRange):
  """
  Plots the convergence graph: iterations vs number of objects.
  Each curve shows the convergence for a given number of columns.
  """
  ########################################################################
  #
  # Accumulate all the results per column in a convergence array.
  #
  # Convergence[c,o] = how long it took it to converge with f unique features
  # and c columns.

  convergence = numpy.zeros((max(columnRange), max(objectRange) + 1))
  for r in results:
    if r["numColumns"] in columnRange:
      convergence[r["numColumns"] - 1, r["numObjects"]] += r["convergencePoint"]

  convergence /= numTrials

  # print "Average convergence array=", convergence

  ########################################################################
  #
  # Create the plot. x-axis=
  plt.figure()
  plotPath = os.path.join("plots", "convergence_by_object_multicolumn.jpg")

  # Plot each curve
  legendList = []
  colorList = ['r', 'b', 'g', 'm', 'c', 'k', 'y']

  for i in range(len(columnRange)):
    c = columnRange[i]
    print "columns={} objectRange={} convergence={}".format(
      c, objectRange, convergence[c-1,objectRange])
    if c == 1:
      legendList.append('1 column')
    else:
      legendList.append('{} columns'.format(c))
    plt.plot(objectRange, convergence[c-1,objectRange],
             color=colorList[i])

  # format
  plt.legend(legendList, loc="upper left", prop={'size':10})
  plt.xlabel("Number of objects in training set")
  plt.xticks(range(0,max(objectRange)+1,10))
  plt.yticks(range(0,int(convergence.max())+2))
  plt.ylabel("Average number of touches")
  plt.title("Object recognition with multiple columns (unique features = 5)")

    # save
  plt.savefig(plotPath)
  plt.close()


if __name__ == "__main__":

  # This is how you run a specific experiment in single process mode. Useful
  # for debugging, profiling, etc.
  if True:
    results = runExperiment(
                  {
                    "numObjects": 30,
                    "numPoints": 10,
                    "numLocations": 10,
                    "numFeatures": 10,
                    "numColumns": 1,
                    "trialNum": 4,
                    "pointRange": 1,
                    "plotInferenceStats": True,  # Outputs detailed graphs
                    "settlingTime": 3,
                    "includeRandomLocation": False
                  }
    )


  # Here we want to see how the number of columns affects convergence.
  # This experiment is run using a process pool
  if False:
    columnRange = [1, 2, 3, 4, 5, 6, 7, 8]
    featureRange = [5, 10, 20, 30]
    objectRange = [100]
    numTrials = 10

    # Comment this out if you are re-running analysis on already saved results
    # Very useful for debugging the plots
    runExperimentPool(
      numObjects=objectRange,
      numLocations=[10],
      numFeatures=featureRange,
      numColumns=columnRange,
      numPoints=10,
      nTrials=numTrials,
      numWorkers=7,
      resultsName="column_convergence_results.pkl")

    with open("column_convergence_results.pkl","rb") as f:
      results = cPickle.load(f)

    plotConvergenceByColumn(results, columnRange, featureRange,
                            numTrials=numTrials)


  # Here we want to see how the number of objects affects convergence for a
  # single column.
  # This experiment is run using a process pool
  if False:
    # We run 10 trials for each column number and then analyze results
    numTrials = 10
    columnRange = [1]
    featureRange = [5,10,20,30]
    objectRange = [2,10,20,30,40,50,60,80,100]

    # Comment this out if you are re-running analysis on already saved results.
    # Very useful for debugging the plots
    runExperimentPool(
                      numObjects=objectRange,
                      numLocations=[10],
                      numFeatures=featureRange,
                      numColumns=columnRange,
                      numPoints=10,
                      nTrials=numTrials,
                      numWorkers=7,
                      resultsName="object_convergence_results.pkl")

    # Analyze results
    with open("object_convergence_results.pkl","rb") as f:
      results = cPickle.load(f)

    plotConvergenceByObject(results, objectRange, featureRange)


  # Here we want to see how the number of objects affects convergence for
  # multiple columns.
  if False:
    # We run 10 trials for each column number and then analyze results
    numTrials = 10
    columnRange = [1,2,4,6]
    featureRange = [5]
    objectRange = [2,5,10,20,30,40,50,60,80,100]

    # Comment this out if you are re-running analysis on already saved results.
    # Very useful for debugging the plots
    runExperimentPool(
                      numObjects=objectRange,
                      numLocations=[10],
                      numFeatures=featureRange,
                      numColumns=columnRange,
                      numPoints=10,
                      numWorkers=7,
                      nTrials=numTrials,
                      resultsName="object_convergence_multi_column_results.pkl")

    # Analyze results
    with open("object_convergence_multi_column_results.pkl","rb") as f:
      results = cPickle.load(f)

    plotConvergenceByObjectMultiColumn(results, objectRange, columnRange)

