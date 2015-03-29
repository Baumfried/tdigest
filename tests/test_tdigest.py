from bintrees import BinaryTree
import pytest
import numpy as np
from numpy import random

from tdigest.tdigest import TDigest, Centroid


@pytest.fixture()
def empty_tdigest():
    return TDigest()


@pytest.fixture()
def example_positive_centroids():
    return BinaryTree([
        (0.5, Centroid(0.5, 1)),
        (1.1, Centroid(1.1, 1)),
        (1.5, Centroid(1.5, 1)),
    ])


@pytest.fixture()
def example_centroids():
    return BinaryTree([
        (-1.1, Centroid(-1.1, 1)),
        (-0.5, Centroid(-0.5, 1)),
        (0.1, Centroid(0.1, 1)),
        (1.5, Centroid(1.5, 1)),
    ])


@pytest.fixture()
def example_random_data():
    return random.randn(100)


class TestTDigest():

    def test_add_centroid(self, empty_tdigest, example_positive_centroids):
        empty_tdigest.C = example_positive_centroids
        new_centroid = Centroid(0.9, 1)
        empty_tdigest._add_centroid(new_centroid)
        assert (empty_tdigest.C - BinaryTree([
            (0.5, Centroid(0.5, 1)),
            (new_centroid.mean, new_centroid),
            (1.1, Centroid(1.1, 1)),
            (1.5, Centroid(1.5, 1)),
        ])).is_empty()

        last_centroid = Centroid(10., 1)
        empty_tdigest._add_centroid(last_centroid)
        assert (empty_tdigest.C - BinaryTree([
            (0.5, Centroid(0.5, 1)),
            (new_centroid.mean, new_centroid),
            (1.1, Centroid(1.1, 1)),
            (1.5, Centroid(1.5, 1)),
            (last_centroid.mean, last_centroid),
        ])).is_empty()

    def test_compute_centroid_quantile(self, empty_tdigest, example_centroids):
        empty_tdigest.C = example_centroids
        empty_tdigest.n = 4

        assert empty_tdigest._compute_centroid_quantile(example_centroids[-1.1]) == (1 / 2. + 0) / 4
        assert empty_tdigest._compute_centroid_quantile(example_centroids[-0.5]) == (1 / 2. + 1) / 4
        assert empty_tdigest._compute_centroid_quantile(example_centroids[0.1]) == (1 / 2. + 2) / 4
        assert empty_tdigest._compute_centroid_quantile(example_centroids[1.5]) == (1 / 2. + 3) / 4



    def test_get_closest_centroids_works_with_positive_values(self, empty_tdigest, example_positive_centroids):
        empty_tdigest.C = example_positive_centroids
        assert empty_tdigest._get_closest_centroids(0.0) == [example_positive_centroids[0.5]]
        assert empty_tdigest._get_closest_centroids(2.0) == [example_positive_centroids[1.5]]
        assert empty_tdigest._get_closest_centroids(1.1) == [example_positive_centroids[1.1]]
        assert empty_tdigest._get_closest_centroids(1.2) == [example_positive_centroids[1.1]]
        assert empty_tdigest._get_closest_centroids(1.4) == [example_positive_centroids[1.5]]
        assert empty_tdigest._get_closest_centroids(1.3) == [example_positive_centroids[1.5], 
                                                             example_positive_centroids[1.1]]


    def test_get_closest_centroids_works_with_negative_values(self, empty_tdigest, example_centroids):
        empty_tdigest.C = example_centroids
        assert empty_tdigest._get_closest_centroids(0.0) == [example_centroids[0.1]]
        assert empty_tdigest._get_closest_centroids(-2.0) == [example_centroids[-1.1]]
        assert empty_tdigest._get_closest_centroids(-0.6) == [example_centroids[-0.5]]
        assert empty_tdigest._get_closest_centroids(-0.4) == [example_centroids[-0.5]]
 

    def test_compress(self, empty_tdigest, example_random_data):
        empty_tdigest.batch_update(example_random_data)
        precompress_n, precompress_len = empty_tdigest.n, len(empty_tdigest)
        empty_tdigest.compress()
        postcompress_n, postcompress_len = empty_tdigest.n, len(empty_tdigest)
        assert postcompress_n == precompress_n
        assert postcompress_len <= precompress_len

class TestStatisticalTests():

    def test_uniform(self):
        T1 = TDigest()
        x = random.random(size=10000)
        T1.batch_update(x)

        assert abs(T1.percentile(.5) - 0.5) < 0.02
        assert abs(T1.percentile(.1) - .1) < 0.01
        assert abs(T1.percentile(.9) - 0.9) < 0.01
        assert abs(T1.percentile(.01) - 0.01) < 0.005
        assert abs(T1.percentile(.99) - 0.99) < 0.005
        assert abs(T1.percentile(.001) - 0.001) < 0.001
        assert abs(T1.percentile(.999) - 0.999) < 0.001
        

class TestCentroid():

    def test_update(self):
        c = Centroid(0, 0)
        value, weight = 1, 1
        c.update(value, weight)
        assert c.count == 1
        assert c.mean == 1

        value, weight = 2, 1
        c.update(value, weight)
        assert c.count == 2
        assert c.mean == (2 + 1.) / 2.

        value, weight = 1, 2
        c.update(value, weight)
        assert c.count == 4
        assert c.mean == 1 * 1 / 4. + 2 * 1 / 4. + 1 * 2 / 4.
