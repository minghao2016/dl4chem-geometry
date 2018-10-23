from __future__ import print_function

import pickle as pkl
import numpy as np
from sklearn.metrics.pairwise import euclidean_distances
import sys, gc, os
import PredX_MPNN as MPNN
import sparse

# hyper-parameters
#data = 'COD' #'COD' or 'QM9'

import argparse
parser = argparse.ArgumentParser(description='Train student network')

parser.add_argument('--data', type=str, default='COD', choices=['COD','QM9'])
parser.add_argument('--dec', type=str, default='npe', choices=['mpnn','npe','none'])
parser.add_argument('--ckptdir', type=str, default='./checkpoints/')
parser.add_argument('--eventdir', type=str, default='./events/')
parser.add_argument('--model-name', type=str, default='test')
parser.add_argument('--alignment-type', type=str, default='kabsch', choices=['default','linear','kabsch'])
parser.add_argument('--virtual-node', action='store_true')
parser.add_argument('--debug', action='store_true', help='debug mode')
parser.add_argument('--dim-h', type=int, default=50, help='dimension of the hidden')
parser.add_argument('--dim-f', type=int, default=100, help='dimension of the hidden')
parser.add_argument('--mpnn-steps', type=int, default=5, help='number of mpnn steps')
parser.add_argument('--mpnn-dec-steps', type=int, default=1, help='number of mpnn steps for decoding')
parser.add_argument('--npe-steps', type=int, default=10, help='number of mpnn steps')
parser.add_argument('--batch-size', type=int, default=20, help='batch size')

args = parser.parse_args()

if args.data == 'COD':
    n_max = 50
    dim_node = 33
    dim_edge = 15
    nval = 3000
    ntst = 3000
elif args.data == 'QM9':
    n_max = 9
    dim_node = 20
    dim_edge = 15
    if args.virtual_node is True:
        n_max += 1
        dim_edge += 1
    ntrn = 100000
    nval = 5000
    ntst = 5000

dim_h = args.dim_h
dim_f = args.dim_f
batch_size = args.batch_size

load_path = None
save_path = os.path.join(args.ckptdir, args.model_name + '_model.ckpt')
event_path = os.path.join(args.eventdir, args.model_name)
#save_path = args.save_dir+data+'_'+str(n_max)+'_'+str(args.dec)+'_model.ckpt'

if args.virtual_node:
    molvec_fname = './'+args.data+'_molvec_'+str(n_max-1)+'_vn.p'
    molset_fname = './'+args.data+'_molset_'+str(n_max-1)+'_vn.p'
else:
    molvec_fname = './'+args.data+'_molvec_'+str(n_max)+'.p'
    molset_fname = './'+args.data+'_molset_'+str(n_max)+'.p'

print('::: load data')
[D1, D2, D3, D4, D5] = pkl.load(open(molvec_fname,'rb'))
D1 = D1.todense()
D2 = D2.todense()
D3 = D3.todense()

ntrn = len(D5)-nval-ntst

[molsup, molsmi] = pkl.load(open(molset_fname,'rb'))

D1_trn = D1[:ntrn]
D2_trn = D2[:ntrn]
D3_trn = D3[:ntrn]
D4_trn = D4[:ntrn]
D5_trn = D5[:ntrn]
molsup_trn =molsup[:ntrn]
D1_val = D1[ntrn:ntrn+nval]
D2_val = D2[ntrn:ntrn+nval]
D3_val = D3[ntrn:ntrn+nval]
D4_val = D4[ntrn:ntrn+nval]
D5_val = D5[ntrn:ntrn+nval]
molsup_val =molsup[ntrn:ntrn+nval]
D1_tst = D1[ntrn+nval:ntrn+nval+ntst]
D2_tst = D2[ntrn+nval:ntrn+nval+ntst]
D3_tst = D3[ntrn+nval:ntrn+nval+ntst]
D4_tst = D4[ntrn+nval:ntrn+nval+ntst]
D5_tst = D5[ntrn+nval:ntrn+nval+ntst]
molsup_tst =molsup[ntrn+nval:ntrn+nval+ntst]

if args.virtual_node:
    tm_trn = np.zeros(D2_trn.shape)
    tm_val = np.zeros(D2_val.shape)
    n_atoms_trn = D2_trn.sum(axis=1)
    n_atoms_val = D2_val.sum(axis=1)
    for i in range(D2_trn.shape[0]):
        tm_trn[i, :n_atoms_trn[i, 0]-1] = 1
    for i in range(D2_val.shape[0]):
        tm_val[i, :n_atoms_val[i, 0]-1] = 1

del D1, D2, D3, D4, D5, molsup

model = MPNN.Model(args.data, n_max, dim_node, dim_edge, dim_h, dim_f, batch_size,\
                    args.dec, mpnn_steps=args.mpnn_steps, mpnn_dec_steps=args.mpnn_dec_steps, npe_steps=args.npe_steps,
                   alignment_type=args.alignment_type, virtual_node=args.virtual_node)

with model.sess:
    if args.virtual_node:
        model.train(D1_trn, D2_trn, D3_trn, D4_trn, D5_trn, molsup_trn, D1_val, D2_val, D3_val, D4_val, D5_val, molsup_val, load_path, save_path, tm_trn, tm_val, event_path, debug=args.debug)
    else:
        model.train(D1_trn, D2_trn, D3_trn, D4_trn, D5_trn, molsup_trn, D1_val, D2_val, D3_val, D4_val, D5_val, molsup_val, load_path, save_path)
    #model.saver.restore( model.sess, save_path )
