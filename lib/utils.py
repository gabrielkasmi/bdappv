import traceback
import threading
from contextlib import closing
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import os, sys
import json

from IPython.core.display import display
from ipywidgets import Output, HBox, Button
from joblib import Parallel, delayed

from progressbar import progressbar
from ipywidgets import HTML, VBox
from plotly import graph_objects as go

from lib.model import parse_dict, to_json
import argparse
from strenum import StrEnum


IMG_URL_PATTERN="https://www.bdpv.fr/_BDapPV/img{Campaign}{Surf}/img{Surf}_{id}.png"
# Default folder
CACHE_FOLDER="img/"
CACHE_PATTERN="{campaign}/{phase}/{id}.png"

class Campaign(StrEnum) :
    GOOGLE="google"
    IGN="ign"

class Phase(StrEnum) :
    CLICK="click"
    SURF="surf"


def fetch(url, params, out) :
    """Fetch a file from an URL"""
    url = url + '?' + urlencode(params)
    req = Request(url)

    with closing(urlopen(req)) as res :
        data = res.read()
        with open(out, 'wb') as out_file:
            out_file.write(data)


def img_path(campaign, phase, id) :
    return os.path.join(CACHE_FOLDER, CACHE_PATTERN.format(id=id, campaign=campaign, phase=phase))



def get_image(id, campaign, phase) :

    """Fetch image of given ID if not present in cache. Return local path"""

    out_path = img_path(campaign, phase, id)

    if not os.path.exists(out_path) :

        folder = os.path.dirname(out_path)
        if not os.path.exists(folder):
            os.makedirs(folder)

        url = IMG_URL_PATTERN.format(
            id=id,
            Surf="" if phase == Phase.CLICK else "Surf",
            Campaign=campaign.capitalize())

        fetch(url, {}, out_path)

    return out_path

class Arg :
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

def eprint(*args) :
    print(*args, file=sys.stderr)


def main_process(img_function, extra_args=[]) :
    """Common parser of input arguments for analysis script.
    Parameters :
        img_function(img) - function called for every image."""

    parser = argparse.ArgumentParser()
    parser.add_argument('input_file', type=str, help="Input file, or '-' for stdin")
    parser.add_argument('output_file', type=str, help="Output file, or '-' for stdout")
    parser.add_argument('--display', "-d", action='store_true', help="Display plots")
    parser.add_argument('--parallel', "-p", action='store_true', help="Parallel compute")
    parser.add_argument('--out', "-o",  metavar='out_dir', help="Output folder for processed images")
    parser.add_argument('--ids', "-i", metavar='id1,id2,id3', help="Filter on ids")

    for arg in extra_args :
        parser.add_argument(*arg.args, **arg.kwargs)

    args = parser.parse_args()

    imgs = load_js(args.input_file)

    if not isinstance(imgs, list) :
        imgs = [imgs]

    outfile = sys.stdout if args.output_file == '-' else open(args.output_file, 'w')
    out_lock = threading.Lock()

    ids = args.ids.split(",") if args.ids else None

    def safe_function(img) :
        if ids and not img.id in ids :
            return
        try :
            out = img_function(img, **vars(args))
            if out is not None :
                with out_lock:
                    to_json(out, outfile)
                    outfile.write(",")

        except Exception as e :
            eprint("Error on img %s" %img.id)
            traceback.print_exc()

    outfile.write("[")

    # Parallel code ?
    if args.parallel :
        scheduler = Parallel(n_jobs=4, backend="threading")
        scheduler(delayed(safe_function)(img) for img in progressbar(imgs))
    else :
        for img in progressbar(imgs) :
            safe_function(img)

    # Delete the last ","
    outfile.seek(outfile.tell() - 1)
    outfile.write("]")




def interactive_plot(df, fig, template, event="hover") :
    """
        Make a plot react on hover or click of a data point and update a HTML preview below it.
        **template** Should be a string and contain placeholders like {colname} to be replaced by the value
        of the corresponding data row
    """

    html = HTML("")

    def update(trace, points, state):
        ind = points.point_inds[0]
        row = df.loc[ind].to_dict()
        html.value = template.format(**row)

    fig = go.FigureWidget(data=fig.data, layout=fig.layout)

    if event == "hover" :
        fig.data[0].on_hover(update)
    else :
        fig.data[0].on_click(update)

    return VBox([fig, html])


def load_js(filename):
    if filename == '-':
        infile = sys.stdin
    else:
        infile = open(filename, 'r')

    js = json.load(infile)

    return parse_dict(js)


def previous_next(items, func, **extra_args) :
    """Meta interactive function to navigate through a list with preivus / next buttons """

    previous_button = Button(description="Previous")
    next_button = Button(description="Next")
    output = Output()

    i = 0

    def show_current() :
        with  output :
            output.clear_output(wait=True)
            func(items[i], **extra_args)

    def previous(*args) :
        nonlocal i
        i -= 1
        show_current()

    def next(*args):
        nonlocal i
        i += 1
        show_current()

    previous_button.on_click(previous)
    next_button.on_click(next)

    show_current()
    display(VBox([
        HBox([previous_button, next_button]),
        output]))





def interactive_plot(df, fig, display_func, event="hover"):
    """
    Make a plot react on hover or click of a data point and update a HTML preview below it.
    **template** Should be a string and contain placeholders like {colname} to be replaced by the value
    of the corresponding data row.

    """

    output = Output()

    def update(trace, points, state):
        ind = points.point_inds[0]
        row = df.loc[ind].to_dict()
        with output :
            output.clear_output(wait=True)
            display_func(row)

    fig = go.FigureWidget(data=fig.data, layout=fig.layout)

    if event == "hover":
        fig.data[0].on_hover(update)
    else:
        fig.data[0].on_click(update)

    return VBox([fig, output])

def print_html(html) :
    display(HTML(html))

