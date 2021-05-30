/*
 * queue.h
 *
 *  Created on: May 30, 2021
 *      Author: ftobler
 */

#ifndef QUEUE_H_
#define QUEUE_H_

template <typename Element> class Queue {
public:
  Queue(int alen);
  ~Queue();
  bool push(Element elem);
  Element pop();
  bool isFull() const;
  bool isEmpty() const;
  int getFreeSpace() const;
  int getMaxLength() const;
  inline int getUsedSpace() const;
private:
  Queue(Queue<Element>& q);  //copy const.
  Element* data;
  int len;
  int start;
  int count;
};

#endif /* QUEUE_H_ */
