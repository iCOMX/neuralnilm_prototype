from __future__ import print_function, division
import matplotlib
matplotlib.use('Agg') # Must be before importing matplotlib.pyplot or pylab!
from neuralnilm import Net, RealApplianceSource, BLSTMLayer, DimshuffleLayer
from lasagne.nonlinearities import sigmoid, rectify
from lasagne.objectives import crossentropy, mse
from lasagne.init import Uniform, Normal
from lasagne.layers import LSTMLayer, DenseLayer, Conv1DLayer, ReshapeLayer, FeaturePoolLayer
from lasagne.updates import nesterov_momentum
from functools import partial
import os
from neuralnilm.source import standardise, discretize, fdiff, power_and_fdiff
from neuralnilm.experiment import run_experiment
from neuralnilm.net import TrainingError
import __main__
from copy import deepcopy
from math import sqrt

NAME = os.path.splitext(os.path.split(__main__.__file__)[1])[0]
PATH = "/homes/dk3810/workspace/python/neuralnilm/figures"
SAVE_PLOT_INTERVAL = 500
GRADIENT_STEPS = 100

"""
e233
based on e131c but with:
* lag=32
* pool

e234
* init final layer and conv layer

235
no lag

236
should be exactly as 131c: no pool, no lag, no init for final and conv layer

237
putting the pool back

238
seems pooling hurts us! disable pooling.
enable lag = 32

239
BLSTM
lag = 20

240
LSTM not BLSTM
various lags

241
output is prediction

260
standardise inputs and outputs.

ideas for next TODO:
* 3 LSTM layers with smaller conv between them
* why does pooling hurt us?
"""

source_dict = dict(
    filename='/data/dk3810/ukdale.h5',
    appliances=[
        ['fridge freezer', 'fridge', 'freezer'], 
        'hair straighteners', 
        'television',
        'dish washer',
        ['washer dryer', 'washing machine']
    ],
    max_appliance_powers=[300, 500, 200, 2500, 2400],
    on_power_thresholds=[5] * 5,
    max_input_power=5900,
    min_on_durations=[60, 60, 60, 1800, 1800],
    min_off_durations=[12, 12, 12, 1800, 600],
    window=("2013-06-01", "2014-07-01"),
    seq_length=1500,
    output_one_appliance=False,
    boolean_targets=False,
    train_buildings=[1],
    validation_buildings=[1], 
    # skip_probability=0.0,
    n_seq_per_batch=50,
    # subsample_target=5,
    include_diff=False,
    clip_appliance_power=True,
    target_is_prediction=False,
    standardise_input = True,
    standardise_targets = True
    #lag=0
)

net_dict = dict(        
    save_plot_interval=SAVE_PLOT_INTERVAL,
    loss_function=mse,
    updates=partial(nesterov_momentum, learning_rate=0.01),
    layers_config=[
        {
            'type': LSTMLayer,
            'num_units': 50,
            'gradient_steps': GRADIENT_STEPS,
            'peepholes': False,
            'W_in_to_cell': Normal(std=1.)
        }
    ]
)


def exp_a(name):
    global source
    # source = RealApplianceSource(**source_dict)
    try:
        a = source
    except NameError:
        source = RealApplianceSource(**source_dict)
    net_dict_copy = deepcopy(net_dict)
    net_dict_copy.update(dict(experiment_name=name, source=source))
    net_dict_copy['layers_config'].append(
        {
            'type': LSTMLayer,
            'num_units': 50,
            'gradient_steps': GRADIENT_STEPS,
            'peepholes': False,
            'W_in_to_cell': Normal(std=(1/sqrt(50)))
        }
    )
    net_dict_copy['layers_config'].append(
        {
            'type': DenseLayer,
            'num_units': source.n_outputs,
            'nonlinearity': None,
            'W': Normal(std=(1/sqrt(50)))
        }
    )
    net = Net(**net_dict_copy)
    return net


def exp_b(name):
    global source
    source = RealApplianceSource(**source_dict)
    try:
        a = source
    except NameError:
        source = RealApplianceSource(**source_dict)
    net_dict_copy = deepcopy(net_dict)
    net_dict_copy.update(dict(experiment_name=name, source=source))
    net_dict_copy['layers_config'].append(
        {
            'type': DenseLayer,
            'num_units': source.n_outputs,
            'nonlinearity': None,
            'W': Normal(std=(1/sqrt(50)))
        }
    )
    net = Net(**net_dict_copy)
    return net



def init_experiment(experiment):
    full_exp_name = NAME + experiment
    func_call = 'exp_{:s}(full_exp_name)'.format(experiment)
    print("***********************************")
    print("Preparing", full_exp_name, "...")
    net = eval(func_call)
    return net


def main():
    for experiment in list('a'):
        full_exp_name = NAME + experiment
        path = os.path.join(PATH, full_exp_name)
        try:
            net = init_experiment(experiment)
            run_experiment(net, path, epochs=5000)
        except KeyboardInterrupt:
            break
        except TrainingError as exception:
            print("EXCEPTION:", exception)
        except Exception as exception:
            print("EXCEPTION:", exception)
            raise


if __name__ == "__main__":
    main()
