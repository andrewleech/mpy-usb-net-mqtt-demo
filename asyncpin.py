# -*- coding: utf-8 -*-
#
# PI Background IP
# Copyright (c) 2020, Planet Innovation
# 436 Elgar Road, Box Hill, 3128, VIC, Australia
# Phone: +61 3 9945 7510
#
# The copyright to the computer program(s) herein is the property of
# Planet Innovation, Australia.
# The program(s) may be used and/or copied only with the written permission
# of Planet Innovation or in accordance with the terms and conditions
# stipulated in the agreement/contract under which the program(s) have been
# supplied.
#

"""
Defines an AsyncPin class for await'ing on external Pin interrupts.
"""

import io
import time

import uasyncio as asyncio
from micropython import const

_MP_STREAM_POLL_RD = const(1)
_MP_STREAM_POLL = const(3)
_MP_STREAM_ERROR = const(-1)


class AsyncPin(io.IOBase):
    """Defines an AsyncPin which can await on a Pin IRQ."""

    def __init__(self, pin, trigger):
        """
        Initialise the AsyncPin object with:
        - pin: must be a Pin object with an irq() method
        - trigger: must be one of IRQ_RISING, IRQ_FALLING or IRQ_RISING|IRQ_FALLING
          (for the combined edges it's not possible to tell which edge occurred, just
          that at least one of them occurred)
        """
        # pylint: disable=super-init-not-called
        self.pin = pin
        self._value = pin.value()
        self._event = asyncio.ThreadSafeFlag()
        self.trigger_ref = self.trigger
        self.pin.irq(self.trigger_ref, trigger, hard=False)

    def trigger(self, _pin=None):
        """Callback for Pin.irq, can be manually called for sw trigger."""
        self._value = self.pin.value()
        self._event.set()

    def value(self, new_value=None):
        """
        This method allows to set and get the value of the pin
        depending on whether the argument new_value is supplied or not.
        """
        if new_value is not None:
            self.pin.value(new_value)
            return None
        return self.pin.value()

    def read(self, _):
        """Access Pin state."""
        return self.pin.value()

    async def wait_edge(self):
        """
        Wait for an edge on the pin.  If there was already an edge since construction
        or the last call to this method then it will return on the next asyncio cycle.
        Otherwise it will block until the pin changes.
        """
        await self._event.wait()
        return self._value


class AsyncPinDb(AsyncPin):
    """Debounced version of AsyncPin."""

    def __init__(self, pin, trigger, debounce_ms=10):
        """
        Initialise the AsyncPin object with:
        - pin: must be a Pin object with an irq() method
        - trigger: must be one of IRQ_RISING, IRQ_FALLING or IRQ_RISING|IRQ_FALLING
          (for the combined edges it's not possible to tell which edge occurred, just
          that at least one of them occurred)
        - debounce_ms: debounce timeout in ms
        """
        self._debounce_ms = debounce_ms
        self._debounce_done = 0
        self._debounce_event = asyncio.ThreadSafeFlag()
        self._debounce_task = asyncio.create_task(self._debounce_fn())

        super().__init__(pin=pin, trigger=trigger)

    async def _debounce_fn(self):
        while True:
            await self._debounce_event.wait()
            self._value = self.pin.value()
            # pylint: disable=no-member
            while time.ticks_diff(time.ticks_ms(), self._debounce_done) < 0:
                await asyncio.sleep_ms(1)
                if self._value != self.pin.value():
                    self._debounce_done = time.ticks_ms() + self._debounce_ms
                    self._value = self.pin.value()
            self._debounce_event.clear()
            self._event.set()

    def trigger(self, _pin=None):
        """Callback for Pin.irq, can be manually called for sw trigger."""
        # pylint: disable=no-member
        self._debounce_done = time.ticks_ms() + self._debounce_ms
        self._debounce_event.set()
