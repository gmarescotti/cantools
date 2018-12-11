from __future__ import print_function
import re
import time

from ...version import __version__


HEADER_FMT = '''\
/**
 * The MIT License (MIT)
 *
 * Copyright (c) 2018 Erik Moqvist
 *
 * Permission is hereby granted, free of charge, to any person
 * obtaining a copy of this software and associated documentation
 * files (the "Software"), to deal in the Software without
 * restriction, including without limitation the rights to use, copy,
 * modify, merge, publish, distribute, sublicense, and/or sell copies
 * of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
 * BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
 * ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
 * CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */

/**
 * This file was generated by cantools version {version} {date}.
 */

#ifndef {include_guard}
#define {include_guard}

#include <stdint.h>
#include <stdbool.h>
#include <unistd.h>

#ifndef EINVAL
#    define EINVAL -22
#endif

{frame_id_defines}
{choices_defines}
{structs}
{declarations}
#endif
'''

SOURCE_FMT = '''\
/**
 * The MIT License (MIT)
 *
 * Copyright (c) 2018 Erik Moqvist
 *
 * Permission is hereby granted, free of charge, to any person
 * obtaining a copy of this software and associated documentation
 * files (the "Software"), to deal in the Software without
 * restriction, including without limitation the rights to use, copy,
 * modify, merge, publish, distribute, sublicense, and/or sell copies
 * of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
 * BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
 * ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
 * CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */

/**
 * This file was generated by cantools version {version} {date}.
 */

#include <string.h>

#include "{header}"

{helpers}\
{definitions}\
'''

STRUCT_FMT = '''\
/**
 * Signals in message {database_message_name}.
 *
{comment}\
 * All signal values are as on the CAN bus.
 */
struct {database_name}_{message_name}_t {{
{members}
}};
'''

DECLARATION_FMT = '''\
/**
 * Pack message {database_message_name}.
 *
 * @param[out] dst_p Buffer to pack the message into.
 * @param[in] src_p Data to pack.
 * @param[in] size Size of dst_p.
 *
 * @return Size of packed data, or negative error code.
 */
ssize_t {database_name}_{message_name}_pack(
    uint8_t *dst_p,
    const struct {database_name}_{message_name}_t *src_p,
    size_t size);

/**
 * Unpack message {database_message_name}.
 *
 * @param[out] dst_p Object to unpack the message into.
 * @param[in] src_p Message to unpack.
 * @param[in] size Size of src_p.
 *
 * @return zero(0) or negative error code.
 */
int {database_name}_{message_name}_unpack(
    struct {database_name}_{message_name}_t *dst_p,
    const uint8_t *src_p,
    size_t size);
'''

SIGNAL_DECLARATION_ENCODE_DECODE_FMT = '''\
/**
 * Encode given signal by applying scaling and offset.
 *
 * @param[in] value Signal to encode.
 *
 * @return Encoded signal.
 */
{type_name} {database_name}_{message_name}_{signal_name}_encode(double value);

/**
 * Decode given signal by applying scaling and offset.
 *
 * @param[in] value Signal to decode.
 *
 * @return Decoded signal.
 */
double {database_name}_{message_name}_{signal_name}_decode({type_name} value);

'''

SIGNAL_DECLARATION_IS_IN_RANGE_FMT = '''\
/**
 * Check that given signal is in allowed range.
 *
 * @param[in] value Signal to check.
 *
 * @return true if in range, false otherwise.
 */
bool {database_name}_{message_name}_{signal_name}_is_in_range({type_name} value);
'''

PACK_HELPER_LEFT_SHIFT_FMT = '''\
static inline uint8_t pack_left_shift_u{length}(
    {var_type} value,
    uint8_t shift,
    uint8_t mask)
{{
    return (uint8_t)((uint8_t)(value << shift) & mask);
}}
'''

PACK_HELPER_RIGHT_SHIFT_FMT = '''\
static inline uint8_t pack_right_shift_u{length}(
    {var_type} value,
    uint8_t shift,
    uint8_t mask)
{{
    return (uint8_t)((uint8_t)(value >> shift) & mask);
}}
'''

UNPACK_HELPER_LEFT_SHIFT_FMT = '''\
static inline {var_type} unpack_left_shift_u{length}(
    uint8_t value,
    uint8_t shift,
    uint8_t mask)
{{
    return ({var_type})(({var_type})(value & mask) << shift);
}}
'''

UNPACK_HELPER_RIGHT_SHIFT_FMT = '''\
static inline {var_type} unpack_right_shift_u{length}(
    uint8_t value,
    uint8_t shift,
    uint8_t mask)
{{
    return ({var_type})(({var_type})(value & mask) >> shift);
}}
'''

DEFINITION_FMT = '''\
ssize_t {database_name}_{message_name}_pack(
    uint8_t *dst_p,
    const struct {database_name}_{message_name}_t *src_p,
    size_t size)
{{
{unused}\
{pack_variables}\
    if (size < {message_length}u) {{
        return (-EINVAL);
    }}

    memset(&dst_p[0], 0, {message_length});
{pack_body}
    return ({message_length});
}}

int {database_name}_{message_name}_unpack(
    struct {database_name}_{message_name}_t *dst_p,
    const uint8_t *src_p,
    size_t size)
{{
{unused}\
{unpack_variables}\
    if (size < {message_length}u) {{
        return (-EINVAL);
    }}

    memset(dst_p, 0, sizeof(*dst_p));
{unpack_body}
    return (0);
}}
'''

SIGNAL_DEFINITION_ENCODE_DECODE_FMT = '''\
{type_name} {database_name}_{message_name}_{signal_name}_encode(double value)
{{
    return ({type_name})({encode});
}}

double {database_name}_{message_name}_{signal_name}_decode({type_name} value)
{{
    return ({decode});
}}

'''

SIGNAL_DEFINITION_IS_IN_RANGE_FMT = '''\
bool {database_name}_{message_name}_{signal_name}_is_in_range({type_name} value)
{{
{unused}\
    return ({check});
}}
'''

EMPTY_DEFINITION_FMT = '''\
ssize_t {database_name}_{message_name}_pack(
    uint8_t *dst_p,
    const struct {database_name}_{message_name}_t *src_p,
    size_t size)
{{
    (void)dst_p;
    (void)src_p;
    (void)size;

    return (0);
}}

int {database_name}_{message_name}_unpack(
    struct {database_name}_{message_name}_t *dst_p,
    const uint8_t *src_p,
    size_t size)
{{
    (void)src_p;
    (void)size;

    memset(dst_p, 0, sizeof(*dst_p));

    return (0);
}}
'''

SIGN_EXTENSION_FMT = '''
    if (({name} & (1{suffix} << {shift})) != 0{suffix}) {{
        {name} |= 0x{mask:x}{suffix};
    }}

'''

SIGNAL_MEMBER_FMT = '''\
    /**
{comment}\
     * Range: {range}
     * Scale: {scale}
     * Offset: {offset}
     */
    {type_name} {name};\
'''


class Signal(object):

    def __init__(self, signal):
        self._signal = signal
        self.snake_name = _camel_to_snake_case(self.name)

    def __getattr__(self, name):
        return getattr(self._signal, name)

    @property
    def unit(self):
        return _get(self._signal.unit, '-')

    @property
    def type_length(self):
        if self.length <= 8:
            return 8
        elif self.length <= 16:
            return 16
        elif self.length <= 32:
            return 32
        else:
            return 64

    @property
    def type_name(self):
        if self.is_float:
            if self.length == 32:
                type_name = 'float'
            else:
                type_name = 'double'
        else:
            type_name = 'int{}_t'.format(self.type_length)

            if not self.is_signed:
                type_name = 'u' + type_name

        return type_name

    @property
    def type_suffix(self):
        try:
            return {
                'uint8_t': 'u',
                'uint16_t': 'u',
                'uint32_t': 'u',
                'int64_t': 'll',
                'uint64_t': 'ull',
                'float': 'f'
            }[self.type_name]
        except KeyError:
            return ''

    @property
    def conversion_type_suffix(self):
        try:
            return {
                8: 'u',
                16: 'u',
                32: 'u',
                64: 'ull'
            }[self.type_length]
        except KeyError:
            return ''

    @property
    def unique_choices(self):
        """Make duplicated choice names unique by first appending its value
        and then underscores until unique.

        """

        items = {
            value: _camel_to_snake_case(name).upper()
            for value, name in self.choices.items()
        }
        names = list(items.values())
        duplicated_names = [
            name
            for name in set(names)
            if names.count(name) > 1
        ]
        unique_choices = {
            value: name
            for value, name in items.items()
            if names.count(name) == 1
        }

        for value, name in items.items():
            if name in duplicated_names:
                name += _canonical('_{}'.format(value))

                while name in unique_choices.values():
                    name += '_'

                unique_choices[value] = name

        return unique_choices

    @property
    def minimum_type_value(self):
        if self.type_name == 'int8_t':
            return -128
        elif self.type_name == 'int16_t':
            return -32768
        elif self.type_name == 'int32_t':
            return -2147483648
        elif self.type_name == 'int64_t':
            return -9223372036854775808
        elif self.type_name[0] == 'u':
            return 0
        else:
            return None

    @property
    def maximum_type_value(self):
        if self.type_name == 'int8_t':
            return 127
        elif self.type_name == 'int16_t':
            return 32767
        elif self.type_name == 'int32_t':
            return 2147483647
        elif self.type_name == 'int64_t':
            return 9223372036854775807
        elif self.type_name == 'uint8_t':
            return 255
        elif self.type_name == 'uint16_t':
            return 65535
        elif self.type_name == 'uint32_t':
            return 4294967295
        elif self.type_name == 'uint64_t':
            return 18446744073709551615
        else:
            return None

    def segments(self, invert_shift):
        index, pos = divmod(self.start, 8)
        left = self.length

        while left > 0:
            if self.byte_order == 'big_endian':
                if left >= (pos + 1):
                    length = (pos + 1)
                    pos = 7
                    shift = -(left - length)
                    mask = ((1 << length) - 1)
                else:
                    length = left
                    shift = (pos - length + 1)
                    mask = ((1 << length) - 1)
                    mask <<= (pos - length + 1)
            else:
                shift = (left - self.length) + pos

                if left >= (8 - pos):
                    length = (8 - pos)
                    mask = ((1 << length) - 1)
                    mask <<= pos
                    pos = 0
                else:
                    length = left
                    mask = ((1 << length) - 1)
                    mask <<= pos

            if invert_shift:
                if shift < 0:
                    shift = -shift
                    shift_direction = 'left'
                else:
                    shift_direction = 'right'
            else:
                if shift < 0:
                    shift = -shift
                    shift_direction = 'right'
                else:
                    shift_direction = 'left'

            yield index, shift, shift_direction, mask

            left -= length
            index += 1


class Message(object):

    def __init__(self, message):
        self._message = message
        self.snake_name = _camel_to_snake_case(self.name)
        self.signals = [Signal(signal)for signal in message.signals]

    def __getattr__(self, name):
        return getattr(self._message, name)

    def get_signal_by_name(self, name):
        for signal in self.signals:
            if signal.name == name:
                return signal


def _canonical(value):
    """Replace anything but 'a-z', 'A-Z' and '0-9' with '_'.

    """

    return re.sub(r'[^a-zA-Z0-9]', '_', value)


def _camel_to_snake_case(value):
    value = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', value)
    value = re.sub(r'(_+)', '_', value)
    value = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', value).lower()
    value = _canonical(value)

    return value


def _strip_blank_lines(lines):
    try:
        while lines[0] == '':
            lines = lines[1:]

        while lines[-1] == '':
            lines = lines[:-1]
    except IndexError:
        pass

    return lines


def _get(value, default):
    if value is None:
        value = default

    return value


def _format_comment(comment):
    if comment:
        return '\n'.join([
            '     * ' + line.rstrip()
            for line in comment.splitlines()
        ]) + '\n     *\n'
    else:
        return ''


def _format_decimal(value, is_float=False):
    if int(value) == value:
        value = int(value)

        if is_float:
            return str(value) + '.0'
        else:
            return str(value)
    else:
        return str(value)


def _format_range(signal):
    minimum = signal.decimal.minimum
    maximum = signal.decimal.maximum
    scale = signal.decimal.scale
    offset = signal.decimal.offset

    if minimum is not None and maximum is not None:
        return '{}..{} ({}..{} {})'.format(
            _format_decimal((minimum - offset) / scale),
            _format_decimal((maximum - offset) / scale),
            minimum,
            maximum,
            signal.unit)
    elif minimum is not None:
        return '{}.. ({}.. {})'.format(
            _format_decimal((minimum - offset) / scale),
            minimum,
            signal.unit)
    elif maximum is not None:
        return '..{} (..{} {}'.format(
            _format_decimal((maximum - offset) / scale),
            maximum,
            signal.unit)
    else:
        return '-'


def _generate_signal(signal):
    comment = _format_comment(signal.comment)
    range_ = _format_range(signal)
    scale = _get(signal.scale, '-')
    offset = _get(signal.offset, '-')

    member = SIGNAL_MEMBER_FMT.format(comment=comment,
                                      range=range_,
                                      scale=scale,
                                      offset=offset,
                                      type_name=signal.type_name,
                                      name=signal.snake_name)

    return member


def _format_pack_code_mux(message,
                          mux,
                          body_lines_per_index,
                          variable_lines,
                          helper_kinds):
    signal_name, multiplexed_signals = list(mux.items())[0]
    _format_pack_code_signal(message,
                             signal_name,
                             body_lines_per_index,
                             variable_lines,
                             helper_kinds)
    multiplexed_signals_per_id = sorted(list(multiplexed_signals.items()))
    signal_name = _camel_to_snake_case(signal_name)

    lines = [
        '',
        'switch (src_p->{}) {{'.format(signal_name)
    ]

    for multiplexer_id, multiplexed_signals in multiplexed_signals_per_id:
        body_lines = _format_pack_code_level(message,
                                             multiplexed_signals,
                                             variable_lines,
                                             helper_kinds)
        lines.append('')
        lines.append('case {}:'.format(multiplexer_id))

        if body_lines:
            lines.extend(body_lines[1:-1])

        lines.append('    break;')

    lines.extend([
        '',
        'default:',
        '    break;',
        '}'])

    return [('    ' + line).rstrip() for line in lines]


def _format_pack_code_signal(message,
                             signal_name,
                             body_lines,
                             variable_lines,
                             helper_kinds):
    signal = message.get_signal_by_name(signal_name)

    if signal.is_float or signal.is_signed:
        variable = '    uint{}_t {};'.format(signal.type_length,
                                             signal.snake_name)

        if signal.is_float:
            conversion = '    memcpy(&{0}, &src_p->{0}, sizeof({0}));'.format(
                signal.snake_name)
        else:
            conversion = '    {0} = (uint{1}_t)src_p->{0};'.format(
                signal.snake_name,
                signal.type_length)

        variable_lines.append(variable)
        body_lines.append(conversion)

    for index, shift, shift_direction, mask in signal.segments(invert_shift=False):
        if signal.is_float or signal.is_signed:
            fmt = '    dst_p[{}] |= pack_{}_shift_u{}({}, {}u, 0x{:02x}u);'
        else:
            fmt = '    dst_p[{}] |= pack_{}_shift_u{}(src_p->{}, {}u, 0x{:02x}u);'

        line = fmt.format(index,
                          shift_direction,
                          signal.type_length,
                          signal.snake_name,
                          shift,
                          mask)
        body_lines.append(line)
        helper_kinds.add((shift_direction, signal.type_length))


def _format_pack_code_level(message,
                            signal_names,
                            variable_lines,
                            helper_kinds):
    """Format one pack level in a signal tree.

    """

    body_lines = []
    muxes_lines = []

    for signal_name in signal_names:
        if isinstance(signal_name, dict):
            mux_lines = _format_pack_code_mux(message,
                                              signal_name,
                                              body_lines,
                                              variable_lines,
                                              helper_kinds)
            muxes_lines += mux_lines
        else:
            _format_pack_code_signal(message,
                                     signal_name,
                                     body_lines,
                                     variable_lines,
                                     helper_kinds)

    body_lines = body_lines + muxes_lines

    if body_lines:
        body_lines = [''] + body_lines + ['']

    return body_lines


def _format_pack_code(message, helper_kinds):
    variable_lines = []
    body_lines = _format_pack_code_level(message,
                                         message.signal_tree,
                                         variable_lines,
                                         helper_kinds)

    if variable_lines:
        variable_lines = sorted(list(set(variable_lines))) + ['', '']

    return '\n'.join(variable_lines), '\n'.join(body_lines)


def _format_unpack_code_mux(message,
                            mux,
                            body_lines_per_index,
                            variable_lines,
                            helper_kinds):
    signal_name, multiplexed_signals = list(mux.items())[0]
    _format_unpack_code_signal(message,
                               signal_name,
                               body_lines_per_index,
                               variable_lines,
                               helper_kinds)
    multiplexed_signals_per_id = sorted(list(multiplexed_signals.items()))
    signal_name = _camel_to_snake_case(signal_name)

    lines = [
        'switch (dst_p->{}) {{'.format(signal_name)
    ]

    for multiplexer_id, multiplexed_signals in multiplexed_signals_per_id:
        body_lines = _format_unpack_code_level(message,
                                               multiplexed_signals,
                                               variable_lines,
                                               helper_kinds)
        lines.append('')
        lines.append('case {}:'.format(multiplexer_id))
        lines.extend(_strip_blank_lines(body_lines))
        lines.append('    break;')

    lines.extend([
        '',
        'default:',
        '    break;',
        '}'])

    return [('    ' + line).rstrip() for line in lines]


def _format_unpack_code_signal(message,
                               signal_name,
                               body_lines,
                               variable_lines,
                               helper_kinds):
    signal = message.get_signal_by_name(signal_name)
    conversion_type_name = 'uint{}_t'.format(signal.type_length)

    if signal.is_float or signal.is_signed:
        variable = '    {} {};'.format(conversion_type_name, signal.snake_name)
        variable_lines.append(variable)
        body_lines.append('    {} = 0{};'.format(signal.snake_name,
                                                 signal.conversion_type_suffix))

    for index, shift, shift_direction, mask in signal.segments(invert_shift=True):
        if signal.is_float or signal.is_signed:
            fmt = '    {} |= unpack_{}_shift_u{}(src_p[{}], {}u, 0x{:02x}u);'
        else:
            fmt = '    dst_p->{} |= unpack_{}_shift_u{}(src_p[{}], {}u, 0x{:02x}u);'

        line = fmt.format(signal.snake_name,
                          shift_direction,
                          signal.type_length,
                          index,
                          shift,
                          mask)
        body_lines.append(line)
        helper_kinds.add((shift_direction, signal.type_length))

    if signal.is_float:
        conversion = '    memcpy(&dst_p->{0}, &{0}, sizeof(dst_p->{0}));'.format(
            signal.snake_name)
        body_lines.append(conversion)
    elif signal.is_signed:
        mask = ((1 << (signal.type_length - signal.length)) - 1)

        if mask != 0:
            mask <<= signal.length
            formatted = SIGN_EXTENSION_FMT.format(name=signal.snake_name,
                                                  shift=signal.length - 1,
                                                  mask=mask,
                                                  suffix=signal.conversion_type_suffix)
            body_lines.extend(formatted.splitlines())

        conversion = '    dst_p->{0} = (int{1}_t){0};'.format(signal.snake_name,
                                                              signal.type_length)
        body_lines.append(conversion)


def _format_unpack_code_level(message,
                              signal_names,
                              variable_lines,
                              helper_kinds):
    """Format one unpack level in a signal tree.

    """

    body_lines = []
    muxes_lines = []

    for signal_name in signal_names:
        if isinstance(signal_name, dict):
            mux_lines = _format_unpack_code_mux(message,
                                                signal_name,
                                                body_lines,
                                                variable_lines,
                                                helper_kinds)

            if muxes_lines:
                muxes_lines.append('')

            muxes_lines += mux_lines
        else:
            _format_unpack_code_signal(message,
                                       signal_name,
                                       body_lines,
                                       variable_lines,
                                       helper_kinds)

    if body_lines:
        if body_lines[-1] != '':
            body_lines.append('')

    if muxes_lines:
        muxes_lines.append('')

    body_lines = body_lines + muxes_lines

    if body_lines:
        body_lines = [''] + body_lines

    return body_lines


def _format_unpack_code(message, helper_kinds):
    variable_lines = []
    body_lines = _format_unpack_code_level(message,
                                           message.signal_tree,
                                           variable_lines,
                                           helper_kinds)

    if variable_lines:
        variable_lines = sorted(list(set(variable_lines))) + ['', '']

    return '\n'.join(variable_lines), '\n'.join(body_lines)


def _generate_struct(message):
    members = []

    for signal in message.signals:
        members.append(_generate_signal(signal))

    if not members:
        members = [
            '    /**\n'
            '     * Dummy signal in empty message.\n'
            '     */\n'
            '    uint8_t dummy;'
        ]

    if message.comment is None:
        comment = ''
    else:
        comment = ' * {}\n *\n'.format(message.comment)

    return comment, members


def _format_choices(signal, signal_name):
    choices = []

    for value, name in sorted(signal.unique_choices.items()):
        if signal.is_signed:
            fmt = '{signal_name}_{name}_CHOICE ({value})'
        else:
            fmt = '{signal_name}_{name}_CHOICE ({value}u)'

        choices.append(fmt.format(signal_name=signal_name.upper(),
                                  name=name,
                                  value=value))

    return choices


def _generate_encode_decode(message):
    encode_decode = []

    for signal in message.signals:
        scale = signal.decimal.scale
        offset = signal.decimal.offset
        formatted_scale = _format_decimal(scale, is_float=True)
        formatted_offset = _format_decimal(offset, is_float=True)

        if offset == 0 and scale == 1:
            encoding = 'value'
            decoding = '(double)value'
        elif offset != 0 and scale != 1:
            encoding = '(value - {}) / {}'.format(formatted_offset,
                                                  formatted_scale)
            decoding = '((double)value * {}) + {}'.format(formatted_scale,
                                                          formatted_offset)
        elif offset != 0:
            encoding = 'value - {}'.format(formatted_offset)
            decoding = '(double)value + {}'.format(formatted_offset)
        else:
            encoding = 'value / {}'.format(formatted_scale)
            decoding = '(double)value * {}'.format(formatted_scale)

        encode_decode.append((encoding, decoding))

    return encode_decode


def _generate_is_in_range(message):
    """Generate range checks for all signals in given message.

    """

    checks = []

    for signal in message.signals:
        scale = signal.decimal.scale
        offset = (signal.decimal.offset / scale)
        minimum = signal.decimal.minimum
        maximum = signal.decimal.maximum

        if minimum is not None:
            minimum = (minimum / scale - offset)

        if maximum is not None:
            maximum = (maximum / scale - offset)

        suffix = signal.type_suffix
        check = []

        if minimum is not None:
            minimum_type_value = signal.minimum_type_value

            if (minimum_type_value is None) or (minimum > minimum_type_value):
                minimum = _format_decimal(minimum, signal.is_float)
                check.append('(value >= {}{})'.format(minimum, suffix))

        if maximum is not None:
            maximum_type_value = signal.maximum_type_value

            if (maximum_type_value is None) or (maximum < maximum_type_value):
                maximum = _format_decimal(maximum, signal.is_float)
                check.append('(value <= {}{})'.format(maximum, suffix))

        if not check:
            check = ['true']
        elif len(check) == 1:
            check = [check[0][1:-1]]

        check = ' && '.join(check)

        checks.append(check)

    return checks


def _generage_frame_id_defines(database_name, messages):
    return '\n'.join([
        '#define {}_{}_FRAME_ID (0x{:02x}u)'.format(
            database_name.upper(),
            message.snake_name.upper(),
            message.frame_id)
        for message in messages
    ])


def _generate_choices_defines(database_name, messages):
    choices_defines = []

    for message in messages:
        for signal in message.signals:
            if signal.choices is None:
                continue

            choices = _format_choices(signal, signal.snake_name)
            signal_choices_defines = '\n'.join([
                '#define {}_{}_{}'.format(database_name.upper(),
                                          message.snake_name.upper(),
                                          choice)
                for choice in choices
            ])
            choices_defines.append(signal_choices_defines)

    choices_defines = '\n\n'.join(choices_defines)

    if choices_defines:
        choices_defines = '\n' + choices_defines + '\n'

    return choices_defines


def _generate_structs(database_name, messages):
    structs = []

    for message in messages:
        comment, members = _generate_struct(message)
        structs.append(
            STRUCT_FMT.format(comment=comment,
                              database_message_name=message.name,
                              message_name=message.snake_name,
                              database_name=database_name,
                              members='\n\n'.join(members)))

    return '\n'.join(structs)


def _generate_declarations(database_name, messages, floating_point_numbers):
    declarations = []

    for message in messages:
        signal_declarations = []

        for signal in message.signals:
            signal_declaration = ''

            if floating_point_numbers:
                signal_declaration = SIGNAL_DECLARATION_ENCODE_DECODE_FMT.format(
                    database_name=database_name,
                    message_name=message.snake_name,
                    signal_name=signal.snake_name,
                    type_name=signal.type_name)

            signal_declaration += SIGNAL_DECLARATION_IS_IN_RANGE_FMT.format(
                database_name=database_name,
                message_name=message.snake_name,
                signal_name=signal.snake_name,
                type_name=signal.type_name)

            signal_declarations.append(signal_declaration)

        declaration = DECLARATION_FMT.format(database_name=database_name,
                                             database_message_name=message.name,
                                             message_name=message.snake_name)

        if signal_declarations:
            declaration += '\n' + '\n'.join(signal_declarations)

        declarations.append(declaration)

    return '\n'.join(declarations)


def _generate_definitions(database_name, messages, floating_point_numbers):
    definitions = []
    pack_helper_kinds = set()
    unpack_helper_kinds = set()

    for message in messages:
        signal_definitions = []

        for signal, (encode, decode), check in zip(message.signals,
                                                   _generate_encode_decode(message),
                                                   _generate_is_in_range(message)):
            if check == 'true':
                unused = '    (void)value;\n\n'
            else:
                unused = ''

            signal_definition = ''

            if floating_point_numbers:
                signal_definition = SIGNAL_DEFINITION_ENCODE_DECODE_FMT.format(
                    database_name=database_name,
                    message_name=message.snake_name,
                    signal_name=signal.snake_name,
                    type_name=signal.type_name,
                    encode=encode,
                    decode=decode)

            signal_definition += SIGNAL_DEFINITION_IS_IN_RANGE_FMT.format(
                database_name=database_name,
                message_name=message.snake_name,
                signal_name=signal.snake_name,
                type_name=signal.type_name,
                unused=unused,
                check=check)

            signal_definitions.append(signal_definition)

        if message.length > 0:
            pack_variables, pack_body = _format_pack_code(message,
                                                          pack_helper_kinds)
            unpack_variables, unpack_body = _format_unpack_code(message,
                                                                unpack_helper_kinds)

            if pack_body:
                unused = ''
            else:
                unused = '    (void)src_p;\n\n'

            definition = DEFINITION_FMT.format(database_name=database_name,
                                               database_message_name=message.name,
                                               message_name=message.snake_name,
                                               message_length=message.length,
                                               unused=unused,
                                               pack_variables=pack_variables,
                                               pack_body=pack_body,
                                               unpack_variables=unpack_variables,
                                               unpack_body=unpack_body)
        else:
            definition = EMPTY_DEFINITION_FMT.format(database_name=database_name,
                                                     message_name=message.snake_name)

        if signal_definitions:
            definition += '\n' + '\n'.join(signal_definitions)

        definitions.append(definition)

    return '\n'.join(definitions), (pack_helper_kinds, unpack_helper_kinds)


def _generate_helpers_kind(kinds, left_format, right_format):
    formats = {
        'left': left_format,
        'right': right_format
    }
    helpers = []

    for shift_direction, length in sorted(kinds):
        var_type = 'uint{}_t'.format(length)
        helper = formats[shift_direction].format(length=length,
                                                 var_type=var_type)
        helpers.append(helper)

    return helpers


def _generate_helpers(kinds):
    pack_helpers = _generate_helpers_kind(kinds[0],
                                          PACK_HELPER_LEFT_SHIFT_FMT,
                                          PACK_HELPER_RIGHT_SHIFT_FMT)
    unpack_helpers = _generate_helpers_kind(kinds[1],
                                            UNPACK_HELPER_LEFT_SHIFT_FMT,
                                            UNPACK_HELPER_RIGHT_SHIFT_FMT)
    helpers = pack_helpers + unpack_helpers

    if helpers:
        helpers.append('')

    return '\n'.join(helpers)


def generate(database,
             database_name,
             header_name,
             floating_point_numbers=True):
    """Generate C source code from given CAN database `database`.

    `database_name` is used as a prefix for all defines, data
    structures and functions.

    `header_name` is the file name of the C header file, which is
    included by the C source file.

    Set `floating_point_numbers` to ``True`` to allow floating point
    numbers in the generated code.

    This function returns a tuple of the C header and source files as
    strings.

    """

    date = time.ctime()
    messages = [Message(message) for message in database.messages]
    include_guard = '{}_H'.format(database_name.upper())
    frame_id_defines = _generage_frame_id_defines(database_name, messages)
    choices_defines = _generate_choices_defines(database_name, messages)
    structs = _generate_structs(database_name, messages)
    declarations = _generate_declarations(database_name,
                                          messages,
                                          floating_point_numbers)
    definitions, helper_kinds = _generate_definitions(database_name,
                                                      messages,
                                                      floating_point_numbers)
    helpers = _generate_helpers(helper_kinds)

    header = HEADER_FMT.format(version=__version__,
                               date=date,
                               include_guard=include_guard,
                               frame_id_defines=frame_id_defines,
                               choices_defines=choices_defines,
                               structs=structs,
                               declarations=declarations)

    source = SOURCE_FMT.format(version=__version__,
                               date=date,
                               header=header_name,
                               helpers=helpers,
                               definitions=definitions)

    return header, source
