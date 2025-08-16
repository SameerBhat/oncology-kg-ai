'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Question, User } from '../../../payload-types';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@sparkcms/shadcn/ui/tooltip';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@sparkcms/shadcn/ui/accordion';
import NodeTooltipViewer from '../../../components/NodeTooltipViewer/NodeTooltipViewer';
import { LazyTreeNode } from '../../../providers/node-type';
import { CommonButton } from '@sparkcms/common/button/CommonButton';

export interface SavedNode {
  id: string;
  text?: string;
  richText?: string;
  notes?: string;
  links?: string[];
  attributes?: Record<string, string>;
  isDuplicate?: boolean;
  isIrrelevant?: boolean;
  isManuallyAdded?: boolean; // Flag to identify nodes that were manually added vs from original model output
  score?: number;
}

/**
 * The shape we will persist to ordered_nodes in the DB.
 *
 * DATA FLOW FOR MANUALLY ADDED NODES:
 * 1. User adds node manually → originalIndex: -1 in UI state
 * 2. Save to DB → stored as {node: {...}, original_index: -1} in ordered_nodes
 * 3. Manually added nodes are also appended to the nodes array with isManuallyAdded: true
 * 4. On reload → buildNodeItems preserves original_index: -1 from ordered_nodes
 * 5. UI correctly shows "manually added" label based on originalIndex: -1
 *
 * We DO NOT mutate the original `answer.nodes` order, but we do append manually added nodes
 * with the isManuallyAdded flag to ensure all node data is available in the nodes array.
 */
export interface OrderedNodeRecord {
  node: string | SavedNode; // can be an id or an embedded node
  original_index: number; // zero-based index from the ORIGINAL `nodes` array (-1 for manually added)
}

export interface Answer {
  id: string;
  question_id?: (string | null) | Question;
  /**
   * The source-of-truth input order. We NEVER change this order in the UI.
   */
  nodes?: (SavedNode | string)[] | null;

  /**
   * The persisted ordered list. It may come back as:
   * - OrderedNodeRecord[] (new format) OR
   * - (SavedNode | string)[] (legacy format)
   */
  ordered_nodes?: (OrderedNodeRecord | SavedNode | string)[] | null;

  model_name?: string | null;
  completed?: boolean | null;
  createdBy?: (string | null) | User;
  updatedBy?: (string | null) | User;
  updatedAt: string;
  createdAt: string;
}

export interface QuestionsClientProps {
  answers: Answer[];
  activeModel?: string;
  availableModels?: string[];
}

interface GroupedAnswers {
  [modelName: string]: Answer[];
}

interface NodeItem {
  id: string;
  node: SavedNode;
  /** zero-based index from ORIGINAL `nodes` array */
  originalIndex: number;
}

interface AnswerState {
  [answerId: string]: {
    isEditing: boolean;
    orderedNodes: NodeItem[];
    isAddingNode: boolean;
    searchQuery: string;
    searchResults: SavedNode[];
  };
}

// --- type guards & helpers ----------------------------------------------------
const isOrderedRecord = (val: unknown): val is OrderedNodeRecord => {
  return !!val && typeof val === 'object' && 'original_index' in val && 'node' in val;
};

const isSavedNode = (val: unknown): val is SavedNode => {
  return !!val && typeof val === 'object' && 'id' in val;
};

const getIdFromRef = (ref: string | SavedNode | OrderedNodeRecord): string | null => {
  if (typeof ref === 'string') return ref;
  if (isOrderedRecord(ref)) {
    const n = ref.node;
    return typeof n === 'string' ? n : (n?.id ?? null);
  }
  if (isSavedNode(ref)) return ref.id;
  return null;
};

/**
 * Build a quick id -> index map for the ORIGINAL `nodes` array
 * Note: Manually added nodes with isManuallyAdded: true may appear in this array,
 * but their originalIndex should always remain -1 from ordered_nodes, not their position here
 */
const buildOriginalIndexMap = (nodes: (SavedNode | string)[]): Map<string, number> => {
  const map = new Map<string, number>();
  nodes.forEach((n, i) => {
    const id = typeof n === 'string' ? n : n?.id;
    if (id) map.set(id, i);
  });
  return map;
};

export const QuestionsClient = ({
  answers,
  activeModel,
  availableModels,
}: QuestionsClientProps) => {
  const router = useRouter();
  const [answerStates, setAnswerStates] = useState<AnswerState>({});
  const [draggedItem, setDraggedItem] = useState<string | null>(null);

  const [isSavingOrder, setIsSavingOrder] = useState(false);

  // Since we now only receive answers for the current model, we can simplify
  const currentModel = activeModel || 'Unknown Model';

  // Create grouped answers object for navigation (using availableModels)
  const groupedAnswers: GroupedAnswers = React.useMemo(() => {
    const grouped: GroupedAnswers = {};
    if (availableModels) {
      availableModels.forEach((model) => {
        grouped[model] = model === currentModel ? answers : [];
      });
    } else {
      grouped[currentModel] = answers;
    }
    return grouped;
  }, [availableModels, currentModel, answers]);

  // --- helpers for initializing ordered nodes (no state changes during render) ---
  const buildNodeItems = React.useCallback((answer: Answer, isEditing = false): NodeItem[] => {
    const nodes = (answer.nodes ?? []) as (SavedNode | string)[]; // ORIGINAL order, never mutated
    const ordered = (answer.ordered_nodes ?? []) as (OrderedNodeRecord | SavedNode | string)[];

    // A map of id -> original index (based STRICTLY on `nodes` order)
    const originalIndexMap = buildOriginalIndexMap(nodes);

    // Decide which list to render: if we already have an `ordered_nodes` list, prefer it.
    const list: (OrderedNodeRecord | SavedNode | string)[] = ordered.length > 0 ? ordered : nodes;

    // Helper to fetch a SavedNode object by id from `nodes` (if provided as string in ordered list)
    const getSavedNodeFromNodes = (id: string): SavedNode | null => {
      const ref = nodes.find((n) => (typeof n === 'string' ? n === id : n?.id === id));
      return typeof ref === 'string' ? null : (ref as SavedNode);
    };

    return list
      .map((ref, currentIndex) => {
        // Normalize to an id and a SavedNode
        let id: string | null = null;
        let node: SavedNode | null = null;
        let storedOriginalIndex: number | null = null;

        if (isOrderedRecord(ref)) {
          id = getIdFromRef(ref);
          node = isSavedNode(ref.node)
            ? (ref.node as SavedNode)
            : id
              ? getSavedNodeFromNodes(id)
              : null;
          storedOriginalIndex = ref.original_index ?? null;
        } else if (typeof ref === 'string') {
          id = ref;
          node = getSavedNodeFromNodes(ref);
        } else if (isSavedNode(ref)) {
          id = ref.id;
          node = ref as SavedNode;
        }

        if (!id || !node) return null; // skip if we can't render a concrete node

        // For ordered records, ALWAYS use the stored original_index
        // This preserves manually added nodes (originalIndex -1) and prevents
        // them from getting new indices when they're added to the nodes array
        // Note: Manually added nodes may appear in the nodes array with isManuallyAdded: true
        // but their originalIndex should always remain -1 in ordered_nodes
        if (isOrderedRecord(ref) && typeof storedOriginalIndex === 'number') {
          return {
            id,
            node,
            originalIndex: storedOriginalIndex,
          } as NodeItem;
        }

        // Fallback: compute from nodes array (for legacy data or direct node references)
        const computedOriginalIndex = originalIndexMap.get(id);
        const originalIndex =
          typeof computedOriginalIndex === 'number' ? computedOriginalIndex : currentIndex;

        return {
          id,
          node,
          originalIndex,
        } as NodeItem;
      })
      .filter((item): item is NodeItem => {
        // Filter out nulls first
        if (!item) return false;
        // In edit mode, show all nodes including duplicates and irrelevant ones
        // In view mode, filter out duplicates but show irrelevant nodes with special styling
        return isEditing ? true : !(item.node.isDuplicate === true);
      });
  }, []); // Empty dependency array since this function doesn't depend on any props or state

  // Initialize per-answer state when answers change (safe location to set state)
  React.useEffect(() => {
    setAnswerStates((prev) => {
      const next = { ...prev };
      for (const answer of answers) {
        if (!next[answer.id]) {
          next[answer.id] = {
            isEditing: false,
            orderedNodes: buildNodeItems(answer),
            isAddingNode: false,
            searchQuery: '',
            searchResults: [],
          };
        }
      }
      return next;
    });
  }, [answers, buildNodeItems]);

  const toggleEditMode = React.useCallback(
    (answerId: string) => {
      setAnswerStates((prev) => {
        const currentState = prev[answerId];
        if (!currentState) return prev;

        const newIsEditing = !currentState.isEditing;
        const answer = answers.find((a) => a.id === answerId);

        return {
          ...prev,
          [answerId]: {
            ...currentState,
            isEditing: newIsEditing,
            // Rebuild nodes based on edit mode to show/hide duplicates
            orderedNodes: answer ? buildNodeItems(answer, newIsEditing) : currentState.orderedNodes,
          },
        };
      });
    },
    [answers, buildNodeItems]
  );

  const toggleDuplicateStatus = React.useCallback((answerId: string, nodeId: string) => {
    setAnswerStates((prev) => {
      const currentState = prev[answerId];
      if (!currentState) return prev;

      const newOrderedNodes = currentState.orderedNodes.map((item) => {
        if (item.id === nodeId) {
          return {
            ...item,
            node: {
              ...item.node,
              isDuplicate: !item.node.isDuplicate,
            },
          };
        }
        return item;
      });

      return {
        ...prev,
        [answerId]: {
          ...currentState,
          orderedNodes: newOrderedNodes,
        },
      };
    });
  }, []);

  const toggleIrrelevantStatus = React.useCallback((answerId: string, nodeId: string) => {
    setAnswerStates((prev) => {
      const currentState = prev[answerId];
      if (!currentState) return prev;

      const newOrderedNodes = currentState.orderedNodes.map((item) => {
        if (item.id === nodeId) {
          return {
            ...item,
            node: {
              ...item.node,
              isIrrelevant: !item.node.isIrrelevant,
            },
          };
        }
        return item;
      });

      return {
        ...prev,
        [answerId]: {
          ...currentState,
          orderedNodes: newOrderedNodes,
        },
      };
    });
  }, []);

  const handleDragStart = React.useCallback((e: React.DragEvent, itemId: string) => {
    setDraggedItem(itemId);
    e.dataTransfer.effectAllowed = 'move';
  }, []);

  const handleDragOver = React.useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  }, []);

  const handleDrop = React.useCallback(
    (e: React.DragEvent, answerId: string, dropIndex: number) => {
      e.preventDefault();
      if (!draggedItem) return;

      setAnswerStates((prev) => {
        const currentState = prev[answerId];
        if (!currentState) return prev;

        const newOrderedNodes = Array.from(currentState.orderedNodes);
        const dragIndex = newOrderedNodes.findIndex((item) => item.id === draggedItem);
        if (dragIndex === -1) return prev;

        const [draggedNode] = newOrderedNodes.splice(dragIndex, 1);
        newOrderedNodes.splice(dropIndex, 0, draggedNode);

        return {
          ...prev,
          [answerId]: {
            ...currentState,
            orderedNodes: newOrderedNodes,
          },
        };
      });

      setDraggedItem(null);
    },
    [draggedItem]
  );

  const moveNode = React.useCallback((answerId: string, fromIndex: number, toIndex: number) => {
    setAnswerStates((prev) => {
      const currentState = prev[answerId];
      if (!currentState) return prev;

      const newOrderedNodes = Array.from(currentState.orderedNodes);
      const [movedItem] = newOrderedNodes.splice(fromIndex, 1);
      newOrderedNodes.splice(toIndex, 0, movedItem);

      return {
        ...prev,
        [answerId]: {
          ...currentState,
          orderedNodes: newOrderedNodes,
        },
      };
    });
  }, []);

  // Typeahead search functions
  const toggleAddingNode = React.useCallback((answerId: string) => {
    setAnswerStates((prev) => {
      const currentState = prev[answerId];
      if (!currentState) return prev;

      return {
        ...prev,
        [answerId]: {
          ...currentState,
          isAddingNode: !currentState.isAddingNode,
          searchQuery: '',
          searchResults: [],
        },
      };
    });
  }, []);

  const handleSearchQueryChange = React.useCallback(async (answerId: string, query: string) => {
    setAnswerStates((prev) => {
      const currentState = prev[answerId];
      if (!currentState) return prev;

      return {
        ...prev,
        [answerId]: {
          ...currentState,
          searchQuery: query,
        },
      };
    });

    // Debounce search to avoid too many API calls
    if (query.length >= 2) {
      try {
        const urQlQuery = query;
        console.log('Searching for nodes with query:', urQlQuery);
        const response = await fetch(
          `/api/nodes?where[nodeid][equals]=${encodeURIComponent(query)}`
        );
        if (response.ok) {
          const data = await response.json();
          setAnswerStates((prev) => {
            const currentState = prev[answerId];
            if (!currentState || currentState.searchQuery !== query) return prev;

            return {
              ...prev,
              [answerId]: {
                ...currentState,
                searchResults: data.docs || [],
              },
            };
          });
        }
      } catch (error) {
        console.error('Error searching nodes:', error);
      }
    } else {
      setAnswerStates((prev) => {
        const currentState = prev[answerId];
        if (!currentState) return prev;

        return {
          ...prev,
          [answerId]: {
            ...currentState,
            searchResults: [],
          },
        };
      });
    }
  }, []);

  const addSelectedNode = React.useCallback((answerId: string, selectedNode: SavedNode) => {
    setAnswerStates((prev) => {
      const currentState = prev[answerId];
      if (!currentState) return prev;

      // Check if node already exists
      const existingNode = currentState.orderedNodes.find((item) => item.id === selectedNode.id);
      if (existingNode) {
        alert('This node is already in the list.');
        return prev;
      }

      // Add to the end of the list with a new original_index (use -1 to indicate manually added)
      const newNodeItem: NodeItem = {
        id: selectedNode.id,
        node: selectedNode,
        originalIndex: -1, // Indicates manually added node
      };

      return {
        ...prev,
        [answerId]: {
          ...currentState,
          orderedNodes: [...currentState.orderedNodes, newNodeItem],
          isAddingNode: false,
          searchQuery: '',
          searchResults: [],
        },
      };
    });
  }, []);

  const saveOrder = React.useCallback(
    async (answer: Answer) => {
      if (isSavingOrder) return; // Prevent multiple saves at once
      setIsSavingOrder(true);
      const state = answerStates[answer.id];
      if (!state) return;

      // Build the payload that includes `original_index` for each item (zero-based)
      // Filter out duplicates when saving to ordered_nodes
      const orderedNodesPayload: OrderedNodeRecord[] = state.orderedNodes
        .filter((item) => !item.node.isDuplicate)
        .map((item) => ({
          node: item.node,
          original_index: item.originalIndex,
        }));

      // Build updated nodes array with the duplicate and irrelevant status
      // We ONLY update the original nodes with status changes, we do NOT add manually added nodes here
      const originalNodes = (answer.nodes ?? []) as (SavedNode | string)[];
      const updatedNodes = originalNodes.map((originalNode) => {
        if (typeof originalNode === 'string') return originalNode;

        // Find the corresponding node in our state to get updated status
        const stateNode = state.orderedNodes.find((item) => item.id === originalNode.id);
        if (stateNode) {
          return {
            ...originalNode,
            isDuplicate: stateNode.node.isDuplicate,
            isIrrelevant: stateNode.node.isIrrelevant,
          };
        }
        return originalNode;
      });

      // Add manually added nodes to the original nodes array with a flag marking them as manually added
      // This is necessary for the backend to have all node data, but they're flagged as manual additions
      // Check to avoid duplicating nodes that are already in the nodes array
      const existingNodeIds = new Set(
        originalNodes.map((node) => (typeof node === 'string' ? node : node.id))
      );

      const manuallyAddedNodes = state.orderedNodes
        .filter((item) => item.originalIndex === -1 && !item.node.isDuplicate)
        .filter((item) => !existingNodeIds.has(item.id)) // Prevent duplicates
        .map((item) => ({
          ...item.node,
          isManuallyAdded: true, // Flag to identify manually added nodes
        }));

      const allUpdatedNodes = [...updatedNodes, ...manuallyAddedNodes];

      try {
        const response = await fetch(`/api/answers/${answer.id}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            nodes: allUpdatedNodes, // Save updated nodes with duplicate/irrelevant status + manually added
            ordered_nodes: orderedNodesPayload, // Save ordered nodes without duplicates
            completed: true,
          }),
        });

        if (response.ok) {
          setAnswerStates((prev) => ({
            ...prev,
            [answer.id]: {
              ...prev[answer.id],
              isEditing: false,
            },
          }));
          alert('Order saved successfully!');
          router.refresh(); // This will refresh the current page
        } else {
          alert('Failed to save order');
        }
      } catch (error) {
        console.error('Error saving order:', error);
        alert(
          'Error saving order. For now, this is just a demo - the backend API needs to be implemented.'
        );
      } finally {
        setIsSavingOrder(false);
      }
    },
    [router, answerStates, isSavingOrder]
  );

  const renderNodeItem = React.useCallback(
    (item: NodeItem, index: number, isEditing: boolean, answerId: string) => {
      const { node, originalIndex } = item;
      const hasChanged = originalIndex !== index;

      return (
        <div
          key={item.id}
          draggable={isEditing}
          onDragStart={(e) => isEditing && handleDragStart(e, item.id)}
          onDragOver={isEditing ? handleDragOver : undefined}
          onDrop={(e) => isEditing && handleDrop(e, answerId, index)}
          onClick={() => {
            console.log('Node clicked:', node);
          }}
          className={`
          flex items-center gap-3 p-4 rounded-lg border transition-all duration-200
          ${
            isEditing
              ? 'bg-blue-50 border-blue-200 hover:bg-blue-100 cursor-move hover:shadow-md'
              : 'bg-white border-gray-200 hover:shadow-sm'
          }
          ${draggedItem === item.id ? 'opacity-50 scale-95' : ''}
          ${hasChanged && !isEditing ? 'ring-1 ring-yellow-300 bg-yellow-50' : ''}
          ${node.isDuplicate ? 'bg-red-50 border-red-200 opacity-75' : ''}
          ${node.isIrrelevant ? 'bg-orange-50 border-orange-200 opacity-75' : ''}
        `}
        >
          {isEditing && (
            <div className="flex flex-col gap-1 px-2">
              <CommonButton
                onClick={() => index > 0 && moveNode(answerId, index, index - 1)}
                disabled={index === 0}
                className="p-1 text-gray-400 hover:text-blue-600 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                title="Move up"
                icon="arrow-up"
              />
              <div className="text-gray-400 text-xs">⋮⋮</div>
              <CommonButton
                onClick={() => {
                  const state = answerStates[answerId];
                  if (state && index < state.orderedNodes.length - 1) {
                    moveNode(answerId, index, index + 1);
                  }
                }}
                disabled={(() => {
                  const state = answerStates[answerId];
                  return !state || index >= state.orderedNodes.length - 1;
                })()}
                className="p-1 text-gray-400 hover:text-blue-600 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                title="Move down"
                icon="arrow-down"
              />
            </div>
          )}

          <div className="flex items-center gap-3">
            <span
              className={`
            px-3 py-1 rounded text-sm font-medium min-w-[50px] text-center
            ${isEditing ? 'bg-blue-100 border border-blue-300 text-blue-800' : 'bg-white border border-gray-300 text-gray-700'}
            ${node.isDuplicate ? 'bg-red-100 border-red-300 text-red-700 line-through' : ''}
            ${node.isIrrelevant ? 'bg-orange-100 border-orange-300 text-orange-700' : ''}
          `}
            >
              #{index + 1}
              {node.isDuplicate ? ' (DUP)' : ''}
              {node.isIrrelevant ? ' (IRR)' : ''}
              {originalIndex === -1 ? ' (ADD)' : ''}
            </span>
            {hasChanged && originalIndex !== -1 && (
              <div className="flex items-center gap-1">
                <span className="text-yellow-600 text-xs">→</span>
                <span className="bg-yellow-100 border border-yellow-300 px-2 py-1 rounded text-xs text-yellow-800">
                  was #{originalIndex + 1}
                </span>
              </div>
            )}
            {originalIndex === -1 && (
              <div className="flex items-center gap-1">
                <span className="text-green-600 text-xs">+</span>
                <span className="bg-green-100 border border-green-300 px-2 py-1 rounded text-xs text-green-800">
                  manually added
                </span>
              </div>
            )}
          </div>

          <div className="flex-1">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <div className="cursor-pointer">
                    <p className="text-sm font-medium text-gray-900 leading-tight">
                      {node.text && node.text?.length > 0 ? node.text : node.richText}
                    </p>
                    {node.richText && node.richText?.length > 0 && (
                      <p className="text-xs text-gray-600 mt-1 leading-relaxed">
                        {node.richText.substring(0, 150)}
                        {node.richText.length > 150 ? '...' : ''}
                      </p>
                    )}
                    {node.notes && (
                      <p className="text-xs text-blue-600 mt-1 italic">
                        📝 {node.notes.substring(0, 100)}
                        {node.notes.length > 100 ? '...' : ''}
                      </p>
                    )}
                  </div>
                </TooltipTrigger>
                <TooltipContent
                  className="bg-transparent text-secondary-foreground"
                  data-tooltip-content
                >
                  <NodeTooltipViewer
                    node={
                      {
                        id: node.id,
                        name:
                          node.text && node.text?.length > 0
                            ? node.text
                            : node.richText || 'Untitled Node',
                        node: {
                          id: node.id,
                          text: node.text,
                          notes: node.notes,
                          links: node.links || [],
                          attributes: node.attributes || {},
                          richContent: node.richText || '',
                        },
                        richContent: node.richText,
                        richText: node.richText,
                        updatedAt: new Date().toISOString(),
                        createdAt: new Date().toISOString(),
                      } as unknown as LazyTreeNode
                    }
                  />
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>

          <div className="flex items-center gap-2">
            {/* add node id label*/}
            <CommonButton variant="link" asChild tooltip="Click to view node in tree">
              <a href={`/doctors/dashboard/freemind/${node.id}`} target="_blank">
                <span className="flex gap-1">
                  <span>ID:</span>
                  <span className="font-mono">{node.id}</span>
                </span>
              </a>
            </CommonButton>
            {node.score && (
              <CommonButton
                variant="ghost"
                tooltip={`Accuracy match predicted by model: ${(node.score * 100).toFixed(1)}%`}
              >
                <div className="flex items-center gap-1 px-2 py-1 bg-green-100 border border-green-300 rounded text-xs cursor-help">
                  <span className="text-green-700 font-medium">
                    {Math.round(node.score * 100)}%
                  </span>
                </div>
              </CommonButton>
            )}
            {isEditing && (
              <>
                <CommonButton
                  size="sm"
                  variant={node.isDuplicate ? 'default' : 'outline'}
                  icon="copy"
                  confirm={{
                    title: node.isDuplicate ? 'Remove Duplicate Mark' : 'Mark as Duplicate',
                    description: node.isDuplicate
                      ? 'Are you sure you want to remove the duplicate mark from this node?'
                      : 'Are you sure you want to mark this node as a duplicate? It will be hidden from the UI and excluded from ordered_nodes.',
                    actions: [
                      {
                        children: node.isDuplicate ? 'Remove Mark' : 'Mark Duplicate',
                        variant: 'default',
                        onClick: () => toggleDuplicateStatus(answerId, item.id),
                      },
                    ],
                  }}
                  className={`text-xs ${node.isDuplicate ? 'bg-red-100 text-red-700 border-red-300' : ''}`}
                >
                  {node.isDuplicate ? 'Unmark' : 'Mark Duplicate'}
                </CommonButton>
                <CommonButton
                  size="sm"
                  variant={node.isIrrelevant ? 'default' : 'outline'}
                  icon="x-circle"
                  confirm={{
                    title: node.isIrrelevant ? 'Remove Irrelevant Mark' : 'Mark as Irrelevant',
                    description: node.isIrrelevant
                      ? 'Are you sure you want to remove the irrelevant mark from this node?'
                      : 'Are you sure you want to mark this node as irrelevant? This will negatively impact the model score for this question.',
                    actions: [
                      {
                        children: node.isIrrelevant ? 'Remove Mark' : 'Mark Irrelevant',
                        variant: 'default',
                        onClick: () => toggleIrrelevantStatus(answerId, item.id),
                      },
                    ],
                  }}
                  className={`text-xs ${node.isIrrelevant ? 'bg-orange-100 text-orange-700 border-orange-300' : ''}`}
                >
                  {node.isIrrelevant ? 'Unmark' : 'Mark Irrelevant'}
                </CommonButton>
              </>
            )}
            {isEditing && <div className="text-xs text-gray-400 opacity-70">Drag to reorder</div>}
          </div>
        </div>
      );
    },
    [
      answerStates,
      toggleDuplicateStatus,
      toggleIrrelevantStatus,
      moveNode,
      draggedItem,
      handleDragStart,
      handleDragOver,
      handleDrop,
    ]
  );

  const renderAnswer = React.useCallback(
    (answer: Answer) => {
      const state = answerStates[answer.id];
      const isCompleted = answer.completed;
      const isEditing = state?.isEditing || false;
      const orderedNodes = state?.orderedNodes || [];

      const question =
        typeof answer.question_id === 'object' && answer.question_id
          ? (answer.question_id as Question)
          : null;

      return (
        <div key={answer.id} className="bg-white rounded-lg border border-gray-200 shadow-sm mb-4">
          <Accordion type="single" collapsible className="w-full">
            <AccordionItem value={`answer-${answer.id}`} className="border-none">
              <AccordionTrigger className="px-6 py-4 hover:no-underline">
                <div className="flex items-center justify-between w-full">
                  <div className="flex items-center gap-3">
                    <h3
                      className="text-lg font-semibold text-gray-900"
                      onClick={() => {
                        console.log(answer.id); // Debug log
                      }}
                    >
                      {question?.question_en} - #{answer.id.slice(-6)}
                    </h3>
                    <div className="flex items-center gap-2">
                      {isCompleted ? (
                        <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs font-medium">
                          ✓ Completed
                        </span>
                      ) : (
                        <span className="bg-gray-100 text-gray-700 px-2 py-1 rounded-full text-xs font-medium">
                          ○ Pending
                        </span>
                      )}
                      {isEditing && (
                        <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs animate-pulse">
                          Editing
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 mr-4">
                    <span className="text-sm text-gray-500">{orderedNodes.length} nodes</span>
                    {question && (
                      <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                        Has Question
                      </span>
                    )}
                  </div>
                </div>
              </AccordionTrigger>

              <AccordionContent className="px-6 pb-6">
                <div className="space-y-6">
                  {/* Question Section */}
                  {question && (
                    <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                      <h4 className="font-medium text-blue-900 mb-2 flex items-center gap-2">
                        <span>❓</span>
                        Question
                      </h4>
                      <p className="text-blue-800 text-sm">EN: {question.question_en}</p>
                      <p className="text-blue-800 text-sm">DE: {question.question_de}</p>
                    </div>
                  )}

                  {/* Action Buttons */}
                  <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-gray-700">Actions:</span>
                    </div>
                    <div className="flex items-center gap-2">
                      {isEditing ? (
                        <>
                          <CommonButton
                            onClick={() => toggleAddingNode(answer.id)}
                            icon="plus"
                            variant={state?.isAddingNode ? 'default' : 'outline'}
                            tooltip="Add a new node via search"
                            className="text-sm font-medium flex items-center gap-2 transition-colors"
                          >
                            {state?.isAddingNode ? 'Cancel Add' : 'Add Node'}
                          </CommonButton>
                          <CommonButton
                            onClick={() => saveOrder(answer)}
                            loading={isSavingOrder}
                            icon="save"
                            tooltip="Save the current order of nodes"
                            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md text-sm font-medium flex items-center gap-2 transition-colors"
                          >
                            Save Order
                          </CommonButton>
                          <CommonButton
                            onClick={() => toggleEditMode(answer.id)}
                            icon="x"
                            tooltip="Cancel editing mode"
                            disabled={isSavingOrder}
                            className="bg-gray-400 hover:bg-gray-500 text-white px-4 py-2 rounded-md text-sm font-medium flex items-center gap-2 transition-colors"
                          >
                            Cancel
                          </CommonButton>
                        </>
                      ) : (
                        <button
                          onClick={() => toggleEditMode(answer.id)}
                          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium flex items-center gap-2 transition-colors"
                        >
                          <span>✏️</span>
                          {isCompleted ? 'Edit Order' : 'Set Order'}
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Typeahead Search Section */}
                  {isEditing && state?.isAddingNode && (
                    <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                      <h4 className="font-medium text-green-900 mb-3 flex items-center gap-2">
                        <span>🔍</span>
                        Search and Add Node
                      </h4>
                      <div className="space-y-3">
                        <input
                          type="text"
                          placeholder="Search for nodes... (minimum 2 characters)"
                          value={state.searchQuery}
                          onChange={(e) => handleSearchQueryChange(answer.id, e.target.value)}
                          className="w-full px-3 py-2 border border-green-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                        />
                        {state.searchResults.length > 0 && (
                          <div className="max-h-64 overflow-y-auto border border-green-300 rounded-md bg-white">
                            {state.searchResults.map((searchNode) => (
                              <div
                                key={searchNode.id}
                                className="p-3 border-b border-green-100 hover:bg-green-50 cursor-pointer transition-colors"
                                onClick={() => addSelectedNode(answer.id, searchNode)}
                              >
                                <div className="flex items-center justify-between">
                                  <div className="flex-1">
                                    <p className="text-sm font-medium text-gray-900">
                                      {searchNode.text || searchNode.richText || 'Untitled'}
                                    </p>
                                    <p className="text-xs text-gray-600 mt-1">
                                      ID: {searchNode.id}
                                    </p>
                                    {searchNode.richText && (
                                      <p className="text-xs text-gray-500 mt-1">
                                        {searchNode.richText.substring(0, 100)}...
                                      </p>
                                    )}
                                  </div>
                                  <CommonButton size="sm" icon="plus" className="ml-2">
                                    Add
                                  </CommonButton>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                        {state.searchQuery.length >= 2 && state.searchResults.length === 0 && (
                          <p className="text-sm text-gray-500 py-2">
                            No nodes found for "{state.searchQuery}"
                          </p>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Node Ordering Section */}
                  <div>
                    <div className="flex items-center gap-2 mb-4">
                      <span className="text-orange-600">📋</span>
                      <h4 className="font-medium text-gray-900">
                        {isEditing ? 'Reorder Nodes (Drag & Drop or use arrows)' : 'Node Order'}
                      </h4>
                    </div>

                    <div
                      className={`space-y-3 p-4 rounded-lg border-2 transition-all ${
                        isEditing
                          ? 'bg-blue-50 border-blue-300 border-dashed'
                          : 'bg-gray-50 border-gray-200'
                      }`}
                    >
                      {orderedNodes.length > 0 ? (
                        orderedNodes.map((item, index) =>
                          renderNodeItem(item, index, isEditing, answer.id)
                        )
                      ) : (
                        <div className="text-center py-8 text-gray-500">
                          <span className="text-3xl mb-3 block">📝</span>
                          <h5 className="font-medium mb-1">No nodes available</h5>
                          <p className="text-sm">Add some nodes to start ordering them.</p>
                        </div>
                      )}
                    </div>

                    {isEditing && orderedNodes.length > 0 && (
                      <div className="mt-3 p-3 bg-blue-100 rounded-lg">
                        <p className="text-blue-800 text-sm flex items-center gap-2">
                          <span>💡</span>
                          <span>
                            <strong>Tip:</strong> Drag nodes or use the arrow buttons to reorder
                            them. Yellow indicators show moved positions.
                          </span>
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </div>
      );
    },
    [
      answerStates,
      renderNodeItem,
      toggleEditMode,
      saveOrder,
      toggleAddingNode,
      handleSearchQueryChange,
      addSelectedNode,
    ]
  );

  if (Object.keys(groupedAnswers).length === 0) {
    return (
      <div className="container mx-auto py-8">
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="text-4xl text-gray-400 mb-4">⚠️</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Answers Found</h3>
              <p className="text-gray-600">
                There are currently no answers available for annotation.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-3">Answer Annotation Tool</h1>
        <p className="text-gray-600 text-lg">
          Review and reorder nodes for model training and evaluation purposes.
        </p>
        <div className="mt-4 flex gap-4 text-sm text-gray-600">
          <div className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-green-500"></span>
            <span>Completed</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-gray-400"></span>
            <span>Pending</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-blue-500"></span>
            <span>Editing</span>
          </div>
        </div>
      </div>

      {/* Custom Tabs */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6" aria-label="Tabs">
            {Object.keys(groupedAnswers).map((modelName) => (
              <button
                key={modelName}
                onClick={() => router.push(`/questions/${encodeURIComponent(modelName)}`)}
                className={`
                  flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors
                  ${
                    currentModel === modelName
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                <span>{modelName}</span>
                {currentModel === modelName && (
                  <span className="bg-gray-100 text-gray-600 px-2 py-1 rounded-full text-xs">
                    {answers.length}
                  </span>
                )}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          <div className="space-y-6">
            <div className="bg-blue-50 rounded-lg border border-blue-200 p-4">
              <h2 className="text-xl font-semibold text-blue-900 mb-2">{currentModel}</h2>
              <p className="text-blue-700">
                {answers.length} answer{answers.length !== 1 ? 's' : ''} available for annotation
              </p>
            </div>

            {answers.map(renderAnswer)}
          </div>
        </div>
      </div>
    </div>
  );
};
