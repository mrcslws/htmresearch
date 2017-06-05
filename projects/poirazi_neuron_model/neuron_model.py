import random
import numpy
import copy
from sklearn.cluster import AgglomerativeClustering
from collections import Counter
from nupic.bindings.math import *

numpy.set_printoptions(threshold=numpy.inf)

def power_nonlinearity(power):
    def l(activations):
        original_activations = copy.deepcopy(activations)
        for i in range(power - 1):
            activations.elementNZMultiply(original_activations)
        return activations
    return l

def threshold_nonlinearity(threshold):
    def l(activations):
        activations.threshold(threshold)
        return activations
    return l

def sigmoid(center, scale):
	return lambda x: 1./(1. + numpy.exp(scale*(center - x)))

def sigmoid_nonlinearity(center, scale):
	def l(activations):
		dense = activations.toDense()
		f = sigmoid(center, scale)
		return SM32(f(dense))
	return l

class Matrix_Neuron(object):
    def __init__(self,
                 size = 10000,
                 num_dendrites = 1000,
                 dendrite_length = 10,
                 dim = 400,
                 nonlinearity = threshold_nonlinearity(6),
                 num_replacement = 25,
                 initial_permanence = 0.5,
                 permanence_threshold = 0.15,
                 perm_dec = 0.0125,
                 perm_inc = 0.02):
        self.size = size
        self.num_dendrites = num_dendrites
        self.dendrite_length = dendrite_length
        self.dim = dim
        self.nonlinearity = nonlinearity
        self.num_replacement = num_replacement
        self.initial_permanence = initial_permanence
        self.permanence_threshold = permanence_threshold
        self.perm_dec = perm_dec
        self.perm_inc = perm_inc
        self.initialize_dendrites()
        self.initialize_permanences()

    def initialize_dendrites(self):
        """
        Initialize all the dendrites of the neuron to a set of random connections
        """
        # Wipe any preexisting connections by creating a new connection matrix
        self.dendrites = SM32()
        self.dendrites.reshape(self.dim, self.num_dendrites)

        for row in range(self.num_dendrites):
            synapses = numpy.random.choice(self.dim, self.dendrite_length, replace = False)
            for synapse in synapses:
                self.dendrites[synapse, row] = 1


    def initialize_permanences(self):
        self.permanences = copy.deepcopy(self.dendrites)
        self.permanences = self.permanences*0.3

    def calculate_activation(self, datapoint):
        """
        Only for a single datapoint
        """

        activations = datapoint * self.dendrites
        activations = self.nonlinearity(activations)
        return activations.sum()

    def choose_substitute_pool(self):
        candidates = numpy.random.choice(self.dim, self.num_replacement)
        return candidates

    def calculate_on_entire_dataset(self, data):
        activations = data * self.dendrites
        activations = self.nonlinearity(activations)
        return activations.rowSums()


    def HTM_style_initialize_on_data(self, data, labels):
        """
        Uses a style of initialization inspired by the temporal memory.  When a new positive example is found,
        a dendrite is chosen and a number of synapses are created to the example.

        This works intelligently with an amount of data larger than the number of available dendrites.
        In this case, data is clustered, and then similar datapoints are allotted to shared dendrites,
        with as many overlapping bits as possible chosen.  In practice, it is still better to simply
        allocate enough dendrites to have one per datapoint, but this method at least allows initialization
        to work on larger amounts of data.
        """
        current_dendrite = 0
        self.dendrites = SM32()
        self.dendrites.reshape(self.dim, self.num_dendrites)

        # We want to avoid training on any negative examples
        data = copy.deepcopy(data)
        data.deleteRows([i for i, v in enumerate(labels) if v != 1])

        if data.nRows() > self.num_dendrites:
            print "Neuron using clustering to initialize dendrites"
            data = data.toDense()
            model = AgglomerativeClustering(n_clusters = self.num_dendrites, affinity = "manhattan", linkage = "average")
            clusters = model.fit_predict(data)
            multisets = [[Counter(), []] for i in range(self.num_dendrites)]
            sparse_data = [[i for i, d in enumerate(datapoint) if d == 1] for datapoint in data]

            for datapoint, cluster in zip(sparse_data, clusters):
                multisets[cluster][0] = multisets[cluster][0] + Counter(datapoint)
                multisets[cluster][1].append(set(datapoint))

            for i, multiset in enumerate(multisets):
                shared_elements = set(map(lambda x: x[0], filter(lambda x: x[1] > 1, multiset[0].most_common(self.dendrite_length))))
                dendrite_connections = shared_elements
                while len(shared_elements) < self.dendrite_length:
                    most_distant_point = multiset[1][numpy.argmin([len(dendrite_connections.intersection(point)) for point in multiset[1]])]
                    new_connection = random.sample(most_distant_point - dendrite_connections, 1)[0]
                    dendrite_connections.add(new_connection)

                for synapse in dendrite_connections:
                    self.dendrites[synapse, current_dendrite] = 1.
                current_dendrite += 1

        else:
            for i in range(data.nRows()):
                ones = data.rowNonZeros(i)[0]
                dendrite_connections = numpy.random.choice(ones, size = self.dendrite_length, replace = False)
                for synapse in dendrite_connections:
                    self.dendrites[synapse, current_dendrite] = 1.

                current_dendrite += 1

        self.initialize_permanences()

    def HTM_style_train_on_data(self, data, labels):
        for i in range(data.nRows()):
            self.HTM_style_train_on_datapoint(data.getSlice(i, i+1, 0, data.nCols()), labels[i])

    def HTM_style_train_on_datapoint(self, datapoint, label):
        """
        Run a version of permanence-based training on a datapoint.  Due to the fixed dendrite count and dendrite length,
        we are forced to more efficiently use each synapse, deleting synapses and resetting them if they are not found useful.
        """
        activations = datapoint * self.dendrites
        self.nonlinearity(activations)

        #activations will quite likely still be sparse if using a threshold nonlinearity, so want to keep it sparse
        activation = numpy.sign(activations.sum())


        if label >= 1 and activation >= 0.5:
            strongest_branch = activations.rowMax(0)[0]
            datapoint.transpose()
            inc_vector = self.dendrites.getSlice(0, self.dim, strongest_branch, strongest_branch + 1) * self.perm_inc
            inc_vector.elementNZMultiply(datapoint)
            dec_vector = self.dendrites.getSlice(0, self.dim, strongest_branch, strongest_branch + 1) * self.perm_dec
            dec_vector.elementNZMultiply(1 - datapoint)



            self.permanences.setSlice(0, strongest_branch, self.permanences.getSlice(0, self.dim, strongest_branch, strongest_branch + 1) + inc_vector - dec_vector)

            positions, scores = self.permanences.colNonZeros(strongest_branch)[0], self.permanences.colNonZeros(strongest_branch)[1]

            for position, score in zip(positions, scores):
                if score < self.permanence_threshold:
                    self.dendrites[position, strongest_branch] = 0
                    self.permanences[position, strongest_branch] = 0
                    new_connection = random.sample(set(datapoint.colNonZeros(0)[0]) - set(self.dendrites.colNonZeros(strongest_branch)[0]), 1)[0]
                    self.dendrites[new_connection, strongest_branch] = 1.
                    self.permanences[new_connection, strongest_branch] = self.initial_permanence


        elif label < 1 and activation >= 0.5:
            # Need to weaken some connections
            strongest_branch = activations.rowMax(0)[0]

            dec_vector = self.dendrites.getSlice(0, self.dim, strongest_branch, strongest_branch + 1) * self.perm_dec
            datapoint.transpose()
            dec_vector.elementNZMultiply(datapoint)
            self.permanences.setSlice(0, strongest_branch, self.permanences.getSlice(0, self.dim, strongest_branch, strongest_branch + 1) - dec_vector)


        elif label >= 1 and activation < 0.5:
            # Need to create some new connections
            weakest_branch = numpy.argmin(self.permanences.colSums())
            if numpy.median(self.permanences.getCol(weakest_branch)) < self.permanence_threshold:
                self.permanences.setColToZero(weakest_branch)
                self.dendrites.setColToZero(weakest_branch)

                ones = datapoint.rowNonZeros(0)[0]
                dendrite_connections = numpy.random.choice(ones, size = self.dendrite_length, replace = False)
                for synapse in dendrite_connections:
                    self.dendrites[synapse, weakest_branch] = 1.
                    self.permanences[synapse, weakest_branch] = self.initial_permanence
