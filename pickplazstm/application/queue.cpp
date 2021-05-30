/*
 * queue.cpp
 *
 *  Created on: May 30, 2021
 *      Author: ftobler
 */


#include "queue.h"


template <typename Element>
Queue<Element>::Queue(int alen) {
  data = new Element[alen];
  len = alen;
  start = 0;
  count = 0;
}

template <typename Element>
Queue<Element>::~Queue() {
  delete data;
}

template <typename Element>
Queue<Element>::Queue(Queue<Element>& q) {
  //nothing ever is allowed to do something here
}

template <typename Element>
bool Queue<Element>::push(Element elem) {
  data[(start + count++) % len] = elem;
  return true;
}

template <typename Element>
Element Queue<Element>::pop() {
  count--;
  int s = start;
  start = (start + 1) % len;
  return data[(s) % len];
}

template <typename Element>
bool Queue<Element>::isFull() const {
  return count >= len;
}

template <typename Element>
bool Queue<Element>::isEmpty() const {
  return count <= 0;
}

template <typename Element>
int Queue<Element>::getFreeSpace() const {
  return len - count;
}

template <typename Element>
int Queue<Element>::getMaxLength() const {
  return len;
}

template <typename Element>
int Queue<Element>::getUsedSpace() const {
  return count;
}
