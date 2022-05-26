# orgtreepubsub

An experiment to collect the AWS organization tree data using a
publish-subscribe framework. The publish-subscribe pattern makes the code easier
to read and makes it easier to extend for new organizations features.

I chose [Pypubsub](https://pypubsub.readthedocs.io/en/v4.0.3/index.html) for the
publish-subscribe framework because it's stable, well-documented and easy to
use.

orgtreepubsub works like an event-based crawler of the AWS organization
structure.

## Drawing

Using networkx's built in drawing it can make very rudimendary drawings of
organization graphs. A small organization is somewhat readable and looks like
this:

![Screenshot of a a AWS organization diagram shown in matplotlib.](2022-05-26-20-19-02.png)

## Concurrency

Pypubsub doesn't have built-in support for concurrency, so a naive
implementation will run each AWS API request serially.

The Organizations APIs permit a small amount of concurrent calls. Neither the
concurrency limit nor the throttling limit is documented, but it can definitely
go faster than one request at a time.

### Solution 1

If I just create a thread wherever I need one, I create too many concurrent API
calls. The APIs throttle. Boto3 sometimes fails with throttling errors.

### Solution 2

I can limit the number of concurrent threads by using a ThreadPoolExecutor.

If I create a ThreadPool executor and call submit in place of creating a thread,
the program exits before any pooled thread starts executing. If I add a long
sleep at the end of the main function, the program completes all the expected
work. But it then hangs until the sleep completes. How long is enough? Eaxctly
as long as it takes to do all the work. But how do I know when that happens?

### Solution 3

I can also limit the number of threads by using a bounded work queue to create
threads. Unless the queue is full, the thread will be created as soon as it is
needed. When the queue is full, the queue will block until one of the other
threads completes.

I thought about that, but it seemed to have the same problem as the second
solution.

### Solution 4

Adapt [Stephen Rauch's example](https://stackoverflow.com/a/41654240/111424).
Instead of using a thread, each subscriber adds a task to a queue.

The main function now creates a ThreadPoolExecutor after setting up the
subscribers. The subscribers instead have access to a queue.

After seeding the futures set, the task queue is checked periodically and new
futures are added to the set from it. Completed futures are removed from the
set. When the futures set is empty, the process is complete.

## Performance

In org with ~120 accounts.

With timeout 0.5 seconds.

1 thread : 0m38.304s, 0m38.792s, 0m38.045s.
2 threads: 0m20.093s, 0m20.497s, 0m20.438s.
4 threads: 0m14.830s, 0m15.635s, 0m19.378s.
8 threads: 0m19.897s! 0m18.543s! 0m16.048s.

! indicates at least one TooManyRequestsException was raised.

With timeout 0.1 seconds.

1 thread : 0m40.666s, 0m37.477s, 0m38.662s.
2 threads: 0m19.842s, 0m20.220s, 0m19.906s.
4 threads: 0m15.706s, 0m15.740s, 0m15.496s.
8 threads: 0m16.482s, 0m18.243s, 0m16.125s.

The sweet spot seems to be 4 threads and timeout 0.1 seconds.

The timeout (dequeuing interval) doesn't appear to have much effect. In fact the
timeout is an upper bound. The task loop stops waiting as soon as as the next
future completes. So the interval probably only has an effect on the first
iteration.

## Prior Art

[Orgcrawler](https://github.com/ucopacme/orgcrawler) provides a data model and
methods for querying AWS Organizations resources: accounts, organizational
units, service control policies. It can execute a custom boto3 payload function
in all specified accounts/regions.

It sounds like a combination of this tool and botocove. It appears to be
abandoned, as it was last committed in April 2020 and has no updates to issues
since then.


## Drawing Options

An AWS Organiziation can be modelled as a graph. How do you draw a graph?

Networkx has some
[built-in drawing](https://networkx.org/documentation/stable/reference/drawing.html),
but discourages it. It recommends some other tools instead.

> Proper graph visualization is hard, and we highly recommend that people
> visualize their graphs with tools dedicated to that task. Notable examples of
> dedicated and fully-featured graph visualization tools are
> [Cytoscape](http://www.cytoscape.org/), [Gephi](https://gephi.org/), Graphviz
> and, for [LaTeX](http://www.latex-project.org/) typesetting,
> [PGF/TikZ](https://sourceforge.net/projects/pgf/). To use these and other such
> tools, you should export your NetworkX graph into a format that can be read by
> those tools. For example, Cytoscape can read the GraphML format, and so,
> `networkx.write_graphml(G, path)` might be an appropriate choice.

A friend recommends D3 with a
[force-directed graph](https://observablehq.com/@d3/force-directed-graph)
example and [github repo](https://github.com/d3/d3-force).

[Creating beautiful stand-alone interactive D3 charts with Python](https://towardsdatascience.com/creating-beautiful-stand-alone-interactive-d3-charts-with-python-804117cb95a7)

[Charming Data](https://www.youtube.com/c/CharmingData/about) is a Youtube
channel with tutorials for Cytoscape.

> My name is Adam and my passion is Dash Plotly. This channel will help you
> become an expert in Dash and teach you how to use data visualization to create
> beautiful dashboards, market your product, and develop your data science
> career.
>
> Dash is a platform for building powerful web-based interactive apps,
> in pure python. It's gaining hundreds of users daily, so join the family and
> subscribe to this channel for access to weekly video tutorials.

[Dash](https://plotly.com/dash/) apps give a point-&-click interface to models written in Python.
