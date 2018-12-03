#!/usr/bin/env python3

import requests
import sys
import time
import subprocess
import os

from multiprocessing.pool import ThreadPool
from random import randint
from subprocess import PIPE


NUM_REQUESTS = 100
NUM_TRIALS   = 5
REQUESTS_URL = 'http://35.188.132.194'
#REQUESTS_URL = 'https://yld.me'


def median(lst):
    if NUM_TRIALS % 2:
        median = times[NUM_TRIALS // 2]
    else:
        median = sum(times[NUM_TRIALS-1:NUM_TRIALS]) / 2

    return median


def run_trials():
    times = []
    for _ in range(NUM_TRIALS):
        times.append(run_requests())

    avg_time = sum(times) / NUM_TRIALS
    print('average total elapsed time: {:.4f}'.format(avg_time))
    print('median  total elapsed time: {:.4f}'.format(median(times)))


def run_requests(fcn):
    for i in range(NUM_REQUESTS):
        create_file(i)
    pool = ThreadPool(min(1000, NUM_REQUESTS))
    for t, status in pool.imap(fcn, range(NUM_REQUESTS)):
        print('time to serve: {:.4f}\tstatus: {}'.format(t , status))
    #print('total elapsed time: {:.4f}\n'.format(elapsed_time))


def request_fcn(i):
    start = time.time()
    r = requests.get(REQUESTS_URL)
    return time.time() - start, r.status_code


def upload_fcn(i):
    args = ['curl', '--data-binary', '@-', REQUESTS_URL + '/paste']
    start = time.time()
    #print(' '.join(args))
    with open('test/test_file_' + str(i), 'r') as f:
        subprocess.run(args, stderr=subprocess.STDOUT, stdin=f)
    return time.time() - start, 200


def create_file(i):
    filename = 'test/test_file_' + str(i)
    if os.path.isfile(filename):
        return filename
    with open(filename, 'w') as f:
        for _ in range(300000):
           f.write(chr(randint(0,255))) # Write a random byte
    print('wrote to test/test_file_' + i)
    return filename


if __name__ == '__main__':
    args = sys.argv[1:]
    while len(args):
        arg = args.pop(0)
        if arg == '--url':
            REQUESTS_URL = args.pop(0)
        if arg == '--num_requests':
            NUM_REQUESTS = args.pop(0)
        if arg == '--num_trials':
            NUM_TRIALS = args.pop(0)
    #run_trials()
    #t = upload_fcn(0, 'run_requests.py')
    t = run_requests(upload_fcn)
    #print(t)
