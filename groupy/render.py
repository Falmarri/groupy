import pystache
import os
from pyramid.asset import resolve_asset_spec
from pyramid.path import (
    caller_package,
    package_path,
    )

class MustacheRendererFactory(object):
  def __init__(self, info):
    self.info = info
    

  def __call__(self, value, system):
    package, filename = resolve_asset_spec(self.info.name)
    template = os.path.join(package_path(self.info.package), filename)
    system.update(value)
    system.update({"str" : str})
    with open(template) as f:
        return pystache.render(f.read(), system)