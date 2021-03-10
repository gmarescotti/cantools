import argparse
import os
import os.path

from .. import database
from ..database.can.c_source import generate
from ..database.can.doc_source import  generate_rst, generate_redmine
from ..database.can.qt_source import generate_qt
from ..database.can.c_source import camel_to_snake_case


def _do_generate_qt_source(args):
    dbase = database.load_file(args.infile,
                               encoding=args.encoding,
                               strict=not args.no_strict)

    if args.database_name is None:
        basename = os.path.basename(args.infile)
        database_name = os.path.splitext(basename)[0]
        database_name = camel_to_snake_case(database_name)
    else:
        database_name = args.database_name

    filename_h = database_name + '_qt.h'
    filename_c = database_name + '_qt.cpp'

    header, source, = generate_qt(
        dbase,
        database_name,
        filename_h,
        filename_c,
        args.signals,
	    args)

    with open(filename_h, 'w') as fout:
        fout.write(header)

    with open(filename_c, 'w') as fout:
        fout.write(source)

    print('Successfully generated {} and {}.'.format(filename_h, filename_c))

def _do_generate_pdf_source(args):
    dbase = database.load_file(args.infile,
                               encoding=args.encoding,
                               strict=not args.no_strict)

    if args.database_name is None:
        basename = os.path.basename(args.infile)
        database_name = os.path.splitext(basename)[0]
        database_name = camel_to_snake_case(database_name)
    else:
        database_name = args.database_name

    filename_rst = database_name + '.rst' # Restructured Text Format
    #filename_pdf = database_name + '.pdf' # Portable Document Format

    rst_content = generate_rst(
        dbase,
        database_name,
        filename_rst,
        args.encoding)

    with open(filename_rst, 'w') as fout:
        fout.write(rst_content)

    try:
        import rst2pdf
        rs2pdf.convert(filename_rst)
    except Exception as e:
        print(e)
    else:
        # print('Successfully generated {} and {}.'.format(filename_rst, filename_pdf))
        print('Successfully generated {}.'.format(filename_rst))

def _do_generate_redmine_source(args):
    dbase = database.load_file(args.infile,
                               encoding=args.encoding,
                               strict=not args.no_strict)

    if args.database_name is None:
        basename = os.path.basename(args.infile)
        database_name = os.path.splitext(basename)[0]
        database_name = camel_to_snake_case(database_name)
    else:
        database_name = args.database_name

    redmine_content = generate_redmine(
        dbase,
        database_name,
        args.encoding)

def _do_generate_c_source(args):
    dbase = database.load_file(args.infile,
                               encoding=args.encoding,
                               strict=not args.no_strict)

    if args.database_name is None:
        basename = os.path.basename(args.infile)
        database_name = os.path.splitext(basename)[0]
        database_name = camel_to_snake_case(database_name)
    else:
        database_name = args.database_name

    filename_h = database_name + '.h'
    filename_c = database_name + '.c'
    fuzzer_filename_c = database_name + '_fuzzer.c'
    fuzzer_filename_mk = database_name + '_fuzzer.mk'

    header, source, fuzzer_source, fuzzer_makefile = generate(
        dbase,
        database_name,
        filename_h,
        filename_c,
        fuzzer_filename_c,
        not args.no_floating_point_numbers,
        args.bit_fields,
        no_range_check=args.no_range_check,
        no_size_and_memset=args.no_size_and_memset)

    os.makedirs(args.output_directory, exist_ok=True)
    
    path_h = os.path.join(args.output_directory, filename_h)
    
    with open(path_h, 'w') as fout:
        fout.write(header)

    path_c = os.path.join(args.output_directory, filename_c)

    with open(path_c, 'w') as fout:
        fout.write(source)

    print('Successfully generated {} and {}.'.format(path_h, path_c))

    if args.generate_fuzzer:
        fuzzer_path_c = os.path.join(args.output_directory, fuzzer_filename_c)

        with open(fuzzer_path_c, 'w') as fout:
            fout.write(fuzzer_source)

        fuzzer_path_mk = os.path.join(args.output_directory, fuzzer_filename_mk)

        with open(fuzzer_filename_mk, 'w') as fout:
            fout.write(fuzzer_makefile)

        print('Successfully generated {} and {}.'.format(fuzzer_path_c,
                                                         fuzzer_path_mk))
        print()
        print(
            'Run "make -f {}" to build and run the fuzzer. Requires a'.format(
                fuzzer_filename_mk))
        print('recent version of clang.')


def add_subparser(subparsers):
    generate_c_source_parser = subparsers.add_parser(
        'generate_c_source',
        description='Generate C source code from given database file.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    generate_c_source_parser.add_argument(
        '--database-name',
        help=('The database name.  Uses the stem of the input file name if not'
              ' specified.'))
    generate_c_source_parser.add_argument(
        '--no-floating-point-numbers',
        action='store_true',
        help='No floating point numbers in the generated code.')
    generate_c_source_parser.add_argument(
        '--bit-fields',
        action='store_true',
        help='Use bit fields to minimize struct sizes.')
    generate_c_source_parser.add_argument(
        '-e', '--encoding',
        help='File encoding.')
    generate_c_source_parser.add_argument(
        '--no-strict',
        action='store_true',
        help='Skip database consistency checks.')
    generate_c_source_parser.add_argument(
        '--no-range-check',
        action='store_true',
        help='Skip range checks.')
    generate_c_source_parser.add_argument(
        '--no-size-and-memset',
        action='store_true',
        help='Do not use size check and zero memset for incoming messages.')
    generate_c_source_parser.add_argument(
        '-f', '--generate-fuzzer',
        action='store_true',
        help='Also generate fuzzer source code.')
    generate_c_source_parser.add_argument(
        '-o', '--output-directory',
        default='.',
        help='Directory in which to write output files.')
    generate_c_source_parser.add_argument(
        'infile',
        help='Input database file.')
    generate_c_source_parser.set_defaults(func=_do_generate_c_source)

    add_qt_subparser(subparsers)
    add_pdf_subparser(subparsers)
    add_redmine_subparser(subparsers)

def add_qt_subparser(subparsers):
    generate_qt_source = subparsers.add_parser(
        'generate_qt_source',
        description='Generate C++ Qt source code from given database file.')
    generate_qt_source.add_argument(
        '--database-name',
        help='The database name (default: input file name).')
    generate_qt_source.add_argument(
        '--signals',
        help='The signals separated by comma.',
        required=True)
    generate_qt_source.add_argument(
        '--no-floating-point-numbers',
        action='store_true',
        help='No floating point numbers in the generated code.')
    generate_qt_source.add_argument(
        '--bit-fields',
        action='store_true',
        help='Use bit fields to minimize struct sizes.')
    generate_qt_source.add_argument(
        '--for-modbus',
        action='store_true',
        help='Generates code for use with modbus in place of canbus.')
    generate_qt_source.add_argument(
        '-e', '--encoding',
        help='File encoding.')
    generate_qt_source.add_argument(
        '--no-strict',
        action='store_true',
        help='Skip database consistency checks.')
    generate_qt_source.add_argument(
        '--no-size-and-memset',
        action='store_true',
        help='Do not use size check and zero memset for incoming messages.')
    generate_qt_source.add_argument(
        'infile',
        help='Input database file.')
    generate_qt_source.set_defaults(func=_do_generate_qt_source)

def add_pdf_subparser(subparsers):
    generate_pdf_source = subparsers.add_parser(
        'generate_pdf',
        description='Generate documentation in PDF for the given database file.')
    generate_pdf_source.add_argument(
        '--database-name',
        help='The database name (default: input file name).')
    generate_pdf_source.add_argument(
        '-e', '--encoding',
        help='File encoding.')
    generate_pdf_source.add_argument(
        '--no-strict',
        action='store_true',
        help='Skip database consistency checks.')
    generate_pdf_source.add_argument(
        'infile',
        help='Input database file.')
    generate_pdf_source.set_defaults(func=_do_generate_pdf_source)

def add_redmine_subparser(subparsers):
    generate_redmine_source = subparsers.add_parser(
        'generate_redmine',
        description='Generate documentation in REDMINE for the given database file.')
    generate_redmine_source.add_argument(
        '--database-name',
        help='The database name (default: input file name).')
    generate_redmine_source.add_argument(
        '-e', '--encoding',
        help='File encoding.')
    generate_redmine_source.add_argument(
        '--no-strict',
        action='store_true',
        help='Skip database consistency checks.')
    generate_redmine_source.add_argument(
        'infile',
        help='Input database file.')
    generate_redmine_source.set_defaults(func=_do_generate_redmine_source)
