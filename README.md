Tabu
====

In order to install the dependencies:

```
    $ sudo apt-get -y install python-numpy python-scipy python-pandas
```

To run the script supply one of the villian teams test files:

```
    $ python main.py data/villain_teams/V2_763.txt
```

To run the script with the budget restriction:

```
    $ WITH_BUDGET=1 python main.py data/villain_teams/V2_763.txt
```

To run for all the instances with and without budget:
```
   $ ./benchmark
```
