# bmu

> A building maintenance unit (BMU) is an automatic, remote-controlled, or
> mechanical device, usually suspended from the roof, which moves
> systematically over some surface of a structure while carrying human window
> washers or mechanical robots to maintain or clean the covered surfaces.

![BMU](bmu.jpg)

Also, a little Flask server modelled on [Homu](https://github.com/barosl/homu)
to trigger Buildbot builds from PRs and report statuses back to GitHub.

## Labels

When running CI over a diverse codebase consisting mostly of dynamic languages,
that will run on homogenous servers and be executed in (mostly) homogenous
browsers, compiling code against different architectures is not necessary.
However, being able to target test suites to scope of code change is useful.
For example, when implementing a new JavaScript function, it doesn’t
necessarily make sense to run the Python unit/functional test suite. We should
[fail fast](https://en.wikipedia.org/wiki/Fail-fast). `bmu` allows developers
to notify Buildbot which builders it needs to run by labelling their PRs.

The labels used by `bmu` are managed by the server and defined in its
configuration file (described below).

## Config

### `bmu`

Tell `bmu` about your repositories and their respective {label -> builder}
mappings with a big YAML blob.

``` yaml
auth: <GITHUB_TOKEN>
namespace: bmu
repos:
  bmcorser:
    bmu:
      - python:
         - unit:
           - yellow
           - blue
         - functional
      - web
```

The above configuration is `bmu`'s own config. You can see in the
`bmcorser/bmu` repo there are two branches of builders (`python` and `web`) and
that the `python` branch has two “sub-branches” (`-> unit` and `->
functional`). The `-> unit` branch also has two silly nodes, `yellow`
and `blue`. From this config config above, the following labels will be
created:

 - `bmu/python`
 - `bmu/python/unit`
 - `bmu/python/unit/yellow`
 - `bmu/python/unit/blue`
 - `bmu/python/functional`
 - `bmu/web`



### Buildbot

