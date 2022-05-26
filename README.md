# orgtreepubsub

An experiment to collect the AWS organization tree data using a
publish-subscribe framework. The publish-subscribe pattern makes the code easier
to read and makes it easier to extend for new organizations features.

## Concurrency

The chosen publish-subscribe framework is Pypubsub because it's well-documented
and easy to use. But it doesn't have built-in support for concurrency, so a
naive implementation will run each AWS API request serially.

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
