/*
 *
 * Copyright (c) 2023 The ZMK Contributors
 * SPDX-License-Identifier: MIT
 *
 * Copied from ZMK v0.3 (app/boards/shields/nice_view). What changed: the
 * pictures are our own, from widgets/art.c, instead of ZMK's balloon or
 * mountain, and they take turns on the screen in a random order.
 *
 */

#include <zephyr/kernel.h>
#include <zephyr/random/random.h>

#include <zephyr/logging/log.h>
LOG_MODULE_DECLARE(zmk, CONFIG_ZMK_LOG_LEVEL);

#include <zmk/battery.h>
#include <zmk/display.h>
#include <zmk/events/usb_conn_state_changed.h>
#include <zmk/event_manager.h>
#include <zmk/events/battery_state_changed.h>
#include <zmk/split/bluetooth/peripheral.h>
#include <zmk/events/split_peripheral_status_changed.h>
#include <zmk/usb.h>
#include <zmk/ble.h>

#include "peripheral_status.h"

// Our pictures for the right half, and how many there are. They are defined in
// widgets/art.c, which make_art.py generates from the image files in art/.
extern const lv_img_dsc_t *const custom_arts[];
extern const size_t custom_arts_count;

// The pictures take turns like a shuffled deck of cards: each round shows every
// picture once, in a random order, then a new round starts. `shown` has one bit
// per picture already shown in this round. It holds 32 bits, so make_art.py
// refuses more than 32 pictures.
static uint32_t shown;
static size_t current_art;

static const lv_img_dsc_t *next_art(void) {
    size_t count = MIN(custom_arts_count, 32);
    uint32_t all = BIT64(count) - 1; // one bit per picture
    uint32_t skip = shown;           // pictures this pick can't choose

    if (shown == all) {
        // Every picture has had its turn: start a new round with all of them,
        // but don't open it with the picture on screen, so that one can't show
        // twice in a row. It gets its turn later in the round.
        shown = 0;
        skip = BIT(current_art);
    }

    // Pick one of the remaining pictures at random.
    size_t pick = sys_rand32_get() % (count - __builtin_popcount(skip));
    for (size_t i = 0; i < count; i++) {
        if (!(skip & BIT(i)) && pick-- == 0) {
            current_art = i;
            break;
        }
    }
    shown |= BIT(current_art);
    return custom_arts[current_art];
}

// LVGL (the graphics library) calls this every
// CONFIG_NICE_VIEW_CUSTOM_WIDGET_ART_INTERVAL_SEC seconds.
static void change_art_cb(lv_timer_t *timer) { lv_img_set_src(timer->user_data, next_art()); }

static sys_slist_t widgets = SYS_SLIST_STATIC_INIT(&widgets);

struct peripheral_status_state {
    bool connected;
};

static void draw_top(lv_obj_t *widget, lv_color_t cbuf[], const struct status_state *state) {
    lv_obj_t *canvas = lv_obj_get_child(widget, 0);

    lv_draw_label_dsc_t label_dsc;
    init_label_dsc(&label_dsc, LVGL_FOREGROUND, &lv_font_montserrat_16, LV_TEXT_ALIGN_RIGHT);
    lv_draw_rect_dsc_t rect_black_dsc;
    init_rect_dsc(&rect_black_dsc, LVGL_BACKGROUND);

    // Fill background
    lv_canvas_draw_rect(canvas, 0, 0, CANVAS_SIZE, CANVAS_SIZE, &rect_black_dsc);

    // Draw battery
    draw_battery(canvas, state);

    // Draw output status
    lv_canvas_draw_text(canvas, 0, 0, CANVAS_SIZE, &label_dsc,
                        state->connected ? LV_SYMBOL_WIFI : LV_SYMBOL_CLOSE);

    // Rotate canvas
    rotate_canvas(canvas, cbuf);
}

static void set_battery_status(struct zmk_widget_status *widget,
                               struct battery_status_state state) {
#if IS_ENABLED(CONFIG_USB_DEVICE_STACK)
    widget->state.charging = state.usb_present;
#endif /* IS_ENABLED(CONFIG_USB_DEVICE_STACK) */

    widget->state.battery = state.level;

    draw_top(widget->obj, widget->cbuf, &widget->state);
}

static void battery_status_update_cb(struct battery_status_state state) {
    struct zmk_widget_status *widget;
    SYS_SLIST_FOR_EACH_CONTAINER(&widgets, widget, node) { set_battery_status(widget, state); }
}

static struct battery_status_state battery_status_get_state(const zmk_event_t *eh) {
    return (struct battery_status_state){
        .level = zmk_battery_state_of_charge(),
#if IS_ENABLED(CONFIG_USB_DEVICE_STACK)
        .usb_present = zmk_usb_is_powered(),
#endif /* IS_ENABLED(CONFIG_USB_DEVICE_STACK) */
    };
}

ZMK_DISPLAY_WIDGET_LISTENER(widget_battery_status, struct battery_status_state,
                            battery_status_update_cb, battery_status_get_state)

ZMK_SUBSCRIPTION(widget_battery_status, zmk_battery_state_changed);
#if IS_ENABLED(CONFIG_USB_DEVICE_STACK)
ZMK_SUBSCRIPTION(widget_battery_status, zmk_usb_conn_state_changed);
#endif /* IS_ENABLED(CONFIG_USB_DEVICE_STACK) */

static struct peripheral_status_state get_state(const zmk_event_t *_eh) {
    return (struct peripheral_status_state){.connected = zmk_split_bt_peripheral_is_connected()};
}

static void set_connection_status(struct zmk_widget_status *widget,
                                  struct peripheral_status_state state) {
    widget->state.connected = state.connected;

    draw_top(widget->obj, widget->cbuf, &widget->state);
}

static void output_status_update_cb(struct peripheral_status_state state) {
    struct zmk_widget_status *widget;
    SYS_SLIST_FOR_EACH_CONTAINER(&widgets, widget, node) { set_connection_status(widget, state); }
}

ZMK_DISPLAY_WIDGET_LISTENER(widget_peripheral_status, struct peripheral_status_state,
                            output_status_update_cb, get_state)
ZMK_SUBSCRIPTION(widget_peripheral_status, zmk_split_peripheral_status_changed);

int zmk_widget_status_init(struct zmk_widget_status *widget, lv_obj_t *parent) {
    widget->obj = lv_obj_create(parent);
    lv_obj_set_size(widget->obj, 160, 68);
    lv_obj_t *top = lv_canvas_create(widget->obj);
    lv_obj_align(top, LV_ALIGN_TOP_RIGHT, 0, 0);
    lv_canvas_set_buffer(top, widget->cbuf, CANVAS_SIZE, CANVAS_SIZE, LV_IMG_CF_TRUE_COLOR);

    // Stock ZMK picks the balloon or the mountain at random here. We pick one of
    // our pictures at random instead, then switch to the next one every
    // CONFIG_NICE_VIEW_CUSTOM_WIDGET_ART_INTERVAL_SEC seconds (0 = never).
    lv_obj_t *art = lv_img_create(widget->obj);
    lv_img_set_src(art, next_art());
    lv_obj_align(art, LV_ALIGN_TOP_LEFT, 0, 0);
    if (CONFIG_NICE_VIEW_CUSTOM_WIDGET_ART_INTERVAL_SEC > 0 && custom_arts_count > 1) {
        lv_timer_create(change_art_cb, CONFIG_NICE_VIEW_CUSTOM_WIDGET_ART_INTERVAL_SEC * 1000, art);
    }

    sys_slist_append(&widgets, &widget->node);
    widget_battery_status_init();
    widget_peripheral_status_init();

    return 0;
}

lv_obj_t *zmk_widget_status_obj(struct zmk_widget_status *widget) { return widget->obj; }
