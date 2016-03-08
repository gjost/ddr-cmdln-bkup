import codecs
import logging
import os

from DDR import config
from DDR import fileio
from DDR import identifier
from DDR import models
from DDR import modules
from DDR import util


def make_tmpdir(tmpdir):
    """Make tmp dir if doesn't exist.
    
    @param tmpdir: Absolute path to dir
    """
    if not os.path.exists(tmpdir):
        os.makedirs(tmpdir)

def export(json_paths, model, csv_path, required_only=False):
    """Write the specified objects' data to CSV.
    
    IMPORTANT: All objects in json_paths must have the same set of fields!
    
    TODO let user specify which fields to write
    TODO confirm that each identifier's class matches object_class
    
    @param json_paths: list of .json files
    @param model: str
    @param csv_path: Absolute path to CSV data file.
    @param required_only: boolean Only required fields.
    """
    object_class = identifier.class_for_name(
        identifier.MODEL_CLASSES[model]['module'],
        identifier.MODEL_CLASSES[model]['class']
    )
    module = modules.Module(identifier.module_for_name(
        identifier.MODEL_REPO_MODELS[model]['module']
    ))
    
    if hasattr(object_class, 'xmp') and not hasattr(object_class, 'mets'):
        # File or subclass
        json_paths = models.sort_file_paths(json_paths)
    else:
        # Entity or subclass
        json_paths = util.natural_sort(json_paths)
    json_paths_len = len(json_paths)
    
    make_tmpdir(os.path.dirname(csv_path))
    
    headers = module.csv_export_fields(required_only)
    # make sure we export 'id' if it's not in model FIELDS (ahem, files)
    if 'id' not in headers:
        headers.insert(0, 'id')
    
    with codecs.open(csv_path, 'wb', 'utf-8') as csvfile:
        writer = fileio.csv_writer(csvfile)
        writer.writerow(headers)
        for n,json_path in enumerate(json_paths):
            i = identifier.Identifier(json_path)
            logging.info('%s/%s - %s' % (n+1, json_paths_len, i.id))
            obj = object_class.from_identifier(i)
            if obj:
                writer.writerow(obj.dump_csv())
    
    return csv_path
