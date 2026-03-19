import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { StatusBadge, PriorityBadge } from '../shared/Badges';
import { ArrowLeft, Send, User, Clock, Edit3, Trash2, Lock, MessageCircle, Paperclip, Image, FileText, Download } from 'lucide-react';
import api from '../../api/client';
import useWebSocket from '../../hooks/useWebSocket';

const STATUSES = ['new', 'open', 'pending', 'on_hold', 'solved', 'closed'];
const PRIORITIES = ['low', 'normal', 'high', 'urgent'];

const ROLE_BADGE_STYLES = {
  requester: 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300',
  agent: 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400',
  admin: 'bg-purple-100 text-purple-700 dark:bg-purple-500/20 dark:text-purple-400',
  manager: 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-400',
};

export default function TicketDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const chatEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const [ticket, setTicket] = useState(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editForm, setEditForm] = useState({});
  const [agents, setAgents] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);

  const fetchTicket = useCallback(async () => {
    try {
      const res = await api.get(`/servicedesk/tickets/${id}/`);
      setTicket(res.data);
      lastResponseCountRef.current = res.data.responses?.length || 0;
      setEditForm({
        status: res.data.status,
        priority: res.data.priority,
        agent: res.data.agent || '',
      });
    } catch {
      navigate('/tickets');
    } finally {
      setLoading(false);
    }
  }, [id, navigate]);

  // Poll for new messages every 5 seconds so the chat updates in real-time.
  // Also attempt WebSocket — when running under Daphne/ASGI it gives instant updates.
  const lastResponseCountRef = useRef(0);

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const res = await api.get(`/servicedesk/tickets/${id}/`);
        const newCount = res.data.responses?.length || 0;
        if (newCount !== lastResponseCountRef.current) {
          lastResponseCountRef.current = newCount;
          setTicket(res.data);
          setEditForm({
            status: res.data.status,
            priority: res.data.priority,
            agent: res.data.agent || '',
          });
        }
      } catch {
        // silently ignore polling errors
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [id]);

  // WebSocket (bonus for ASGI deployments)
  const handleWsMessage = useCallback((data) => {
    if (data.type === 'chat_message' || data.type === 'ticket_updated') {
      fetchTicket();
    }
  }, [fetchTicket]);

  useWebSocket(
    id ? `/ws/tickets/${id}/` : null,
    { onMessage: handleWsMessage }
  );

  const role = user?.role;
  const canEdit = role === 'admin' || role === 'agent' || role === 'manager';
  const canEditStatus = role === 'admin' || role === 'agent';
  const canEditPriority = role === 'admin';
  const canAssign = role === 'admin' || role === 'manager';
  const canDelete = role === 'admin';

  const isClosed = ticket?.status === 'solved' || ticket?.status === 'closed';
  const hasAgent = ticket?.agent !== null && ticket?.agent !== undefined;

  const canSendMessage =
    hasAgent &&
    !isClosed &&
    (user?.id === ticket?.requester ||
      user?.id === ticket?.agent ||
      role === 'admin' ||
      role === 'manager');

  useEffect(() => {
    fetchTicket();
    if (canAssign) fetchAgents();
  }, [id]);

  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [ticket?.responses]);

  const fetchAgents = async () => {
    try {
      const res = await api.get('/accounts/users/');
      setAgents(res.data.filter((u) => u.role === 'agent'));
    } catch {}
  };

  const filteredAgents = ticket?.department_id
    ? agents.filter((a) => a.department === ticket.department_id)
    : agents;

  const handleUpdate = async () => {
    try {
      const payload = { ...editForm };
      if (payload.agent === '') payload.agent = null;
      await api.patch(`/servicedesk/tickets/${id}/`, payload);
      setEditing(false);
      fetchTicket();
    } catch {}
  };

  const chatTextareaRef = useRef(null);

  const handleResponse = async (e) => {
    e.preventDefault();
    if (!message.trim() || !canSendMessage) return;
    setSending(true);
    try {
      await api.post(`/servicedesk/tickets/${id}/responses/`, { message });
      setMessage('');
      if (chatTextareaRef.current) {
        chatTextareaRef.current.style.height = 'auto';
      }
      fetchTicket();
    } catch {}
    setSending(false);
  };

  const handleDelete = async () => {
    if (!confirm('Delete this ticket permanently?')) return;
    try {
      await api.delete(`/servicedesk/tickets/${id}/`);
      navigate('/tickets');
    } catch {}
  };

  const handleFileUpload = async (file) => {
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    setSending(true);
    try {
      await api.post(`/servicedesk/tickets/${id}/attachments/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setSelectedFile(null);
      fetchTicket();
    } catch (err) {
      const msg = err.response?.data?.file?.[0] || 'Failed to upload file';
      alert(msg);
    }
    setSending(false);
  };

  const formatTimestamp = (dateStr) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-400">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-slate-300 dark:border-slate-600 border-t-blue-500 rounded-full animate-spin" />
          <span className="text-sm">Loading ticket...</span>
        </div>
      </div>
    );
  }
  if (!ticket) return null;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate(-1)}
          className="p-2 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-500 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="flex-1 min-w-0">
          <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">{ticket.reference_id || `Ticket #${ticket.id}`}</p>
          <h1 className="text-xl font-semibold text-slate-900 dark:text-white truncate">
            {ticket.title}
          </h1>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          {canEdit && !editing && (
            <button
              onClick={() => setEditing(true)}
              className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-lg border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            >
              <Edit3 className="w-4 h-4" /> Edit
            </button>
          )}
          {canDelete && (
            <button
              onClick={handleDelete}
              className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-lg border border-red-200 dark:border-red-500/30 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors"
            >
              <Trash2 className="w-4 h-4" /> Delete
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main content */}
        <div className={`lg:col-span-2 space-y-6 ${editing ? 'order-2 lg:order-1' : ''}`}>
          {/* Description card */}
          <div className="bg-white dark:bg-[#0f1729] rounded-xl border border-slate-200 dark:border-slate-800 p-6">
            <h2 className="text-sm font-semibold text-slate-900 dark:text-white mb-3">
              Description
            </h2>
            <p className="text-sm text-slate-600 dark:text-slate-300 whitespace-pre-wrap leading-relaxed">
              {ticket.description}
            </p>
          </div>

          {/* Chat window */}
          <div className="bg-white dark:bg-[#0f1729] rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden">
            {/* Chat header */}
            <div className="flex items-center gap-2 px-6 py-4 border-b border-slate-200 dark:border-slate-800">
              <MessageCircle className="w-4 h-4 text-slate-500 dark:text-slate-400" />
              <h2 className="text-sm font-semibold text-slate-900 dark:text-white">
                Conversation
              </h2>
              <span className="text-xs text-slate-400 dark:text-slate-500">
                ({ticket.responses?.length || 0} messages)
              </span>
            </div>

            {!hasAgent ? (
              /* Waiting for assignment state */
              <div className="flex flex-col items-center justify-center py-16 px-6">
                <div className="w-14 h-14 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center mb-4">
                  <User className="w-7 h-7 text-slate-400 dark:text-slate-500" />
                </div>
                <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
                  Waiting for assignment...
                </p>
                <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">
                  A support agent will be assigned to this ticket shortly.
                </p>
              </div>
            ) : (
              <>
                {/* Chat messages area */}
                <div className="px-6 py-4 space-y-4 max-h-[28rem] overflow-y-auto">
                  {(!ticket.responses || ticket.responses.length === 0) ? (
                    <div className="flex flex-col items-center justify-center py-12">
                      <MessageCircle className="w-10 h-10 text-slate-300 dark:text-slate-600 mb-3" />
                      <p className="text-sm text-slate-400 dark:text-slate-500">
                        No messages yet. Start the conversation below.
                      </p>
                    </div>
                  ) : (
                    (ticket.responses || []).map((r) => {
                      const isCurrentUser = Number(r.responder) === Number(user?.id);
                      const roleBadgeStyle =
                        ROLE_BADGE_STYLES[r.responder_role] || ROLE_BADGE_STYLES.requester;

                      return (
                        <div
                          key={r.id}
                          className={`flex items-end gap-2.5 ${isCurrentUser ? 'flex-row-reverse' : 'flex-row'}`}
                        >
                          {/* Avatar */}
                          <div
                            className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                              isCurrentUser
                                ? 'bg-blue-100 dark:bg-blue-500/20'
                                : 'bg-slate-200 dark:bg-slate-700'
                            }`}
                          >
                            <User
                              className={`w-4 h-4 ${
                                isCurrentUser
                                  ? 'text-blue-600 dark:text-blue-400'
                                  : 'text-slate-500 dark:text-slate-400'
                              }`}
                            />
                          </div>

                          {/* Message bubble */}
                          <div
                            className={`max-w-[75%] rounded-2xl px-4 py-2.5 ${
                              isCurrentUser
                                ? 'bg-blue-600 text-white rounded-br-md'
                                : 'bg-slate-100 dark:bg-slate-800/80 text-slate-900 dark:text-slate-100 rounded-bl-md'
                            }`}
                          >
                            {/* Sender info */}
                            <div
                              className={`flex items-center gap-2 mb-1 ${
                                isCurrentUser ? 'justify-end' : 'justify-start'
                              }`}
                            >
                              <span
                                className={`text-xs font-semibold ${
                                  isCurrentUser ? 'text-blue-100' : 'text-slate-700 dark:text-slate-300'
                                }`}
                              >
                                {r.responder_name || `User #${r.responder}`}
                              </span>
                              <span
                                className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium capitalize ${
                                  isCurrentUser
                                    ? 'bg-blue-500/40 text-blue-100'
                                    : roleBadgeStyle
                                }`}
                              >
                                {r.responder_role}
                              </span>
                            </div>

                            {/* Message text */}
                            <p
                              className={`text-sm whitespace-pre-wrap leading-relaxed ${
                                isCurrentUser ? 'text-white' : 'text-slate-700 dark:text-slate-200'
                              }`}
                            >
                              {r.message}
                            </p>

                            {/* Timestamp */}
                            <p
                              className={`text-[10px] mt-1 ${
                                isCurrentUser ? 'text-blue-200 text-right' : 'text-slate-400 dark:text-slate-500'
                              }`}
                            >
                              {formatTimestamp(r.created_at)}
                            </p>
                          </div>
                        </div>
                      );
                    })
                  )}
                  <div ref={chatEndRef} />
                </div>

                {/* Attachments */}
                {ticket.attachments && ticket.attachments.length > 0 && (
                  <div className="border-t border-slate-200 dark:border-slate-800 px-6 py-3">
                    <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-2">Attachments</p>
                    <div className="flex flex-wrap gap-2">
                      {ticket.attachments.map((att) => (
                        <a
                          key={att.id}
                          href={att.file}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors text-sm text-slate-600 dark:text-slate-300"
                        >
                          {att.file_type === 'image' ? <Image className="w-4 h-4 text-blue-500" /> : <FileText className="w-4 h-4 text-amber-500" />}
                          <span className="truncate max-w-[150px]">{att.original_filename || 'Attachment'}</span>
                          <Download className="w-3 h-3 text-slate-400" />
                        </a>
                      ))}
                    </div>
                  </div>
                )}

                {/* Chat input area */}
                <div className="border-t border-slate-200 dark:border-slate-800 px-6 py-4">
                  {isClosed ? (
                    <div className="flex items-center justify-center gap-2 py-3 px-4 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700">
                      <Lock className="w-4 h-4 text-slate-400 dark:text-slate-500" />
                      <span className="text-sm text-slate-500 dark:text-slate-400">
                        This conversation has been closed
                      </span>
                    </div>
                  ) : canSendMessage ? (
                    <form onSubmit={handleResponse} className="flex items-end gap-2">
                      <div className="flex-1 relative">
                        <textarea
                          ref={chatTextareaRef}
                          rows={1}
                          value={message}
                          onChange={(e) => {
                            setMessage(e.target.value);
                            e.target.style.height = 'auto';
                            e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
                          }}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                              e.preventDefault();
                              if (message.trim() && !sending) handleResponse(e);
                            }
                          }}
                          placeholder="Type a message..."
                          className="w-full px-4 py-2.5 text-sm rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none overflow-hidden"
                        />
                      </div>
                      <input
                        type="file"
                        ref={fileInputRef}
                        className="hidden"
                        accept=".jpg,.jpeg,.png,.gif,.webp,.pdf,.doc,.docx,.xls,.xlsx,.txt,.csv,.ppt,.pptx"
                        onChange={(e) => {
                          const file = e.target.files[0];
                          if (file) {
                            setSelectedFile(file);
                            handleFileUpload(file);
                          }
                        }}
                      />
                      <button
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                        className="p-2.5 rounded-xl text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors flex-shrink-0"
                        title="Attach file"
                      >
                        <Paperclip className="w-4 h-4" />
                      </button>
                      <button
                        type="submit"
                        disabled={sending || !message.trim()}
                        className="p-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex-shrink-0"
                      >
                        <Send className="w-4 h-4" />
                      </button>
                    </form>
                  ) : (
                    <div className="flex items-center justify-center py-3 px-4 rounded-lg bg-slate-50 dark:bg-slate-800/50">
                      <span className="text-sm text-slate-400 dark:text-slate-500">
                        You do not have permission to send messages on this ticket.
                      </span>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div className={`space-y-6 ${editing ? 'order-1 lg:order-2' : ''}`}>
          <div className="bg-white dark:bg-[#0f1729] rounded-xl border border-slate-200 dark:border-slate-800 p-6 space-y-4">
            <h2 className="text-sm font-semibold text-slate-900 dark:text-white">Details</h2>

            {editing ? (
              <div className="space-y-3">
                {canEditStatus && (
                <div>
                  <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">
                    Status
                  </label>
                  <select
                    value={editForm.status}
                    onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  >
                    {STATUSES.map((s) => (
                      <option key={s} value={s}>
                        {s.replace(/_/g, ' ')}
                      </option>
                    ))}
                  </select>
                </div>
                )}
                {canEditPriority && (
                <div>
                  <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">
                    Priority
                  </label>
                  <select
                    value={editForm.priority}
                    onChange={(e) => setEditForm({ ...editForm, priority: e.target.value })}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  >
                    {PRIORITIES.map((p) => (
                      <option key={p} value={p}>
                        {p}
                      </option>
                    ))}
                  </select>
                </div>
                )}
                {canAssign && (
                  <div>
                    <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">
                      Assign Agent
                    </label>
                    <select
                      value={editForm.agent}
                      onChange={(e) => setEditForm({ ...editForm, agent: e.target.value })}
                      className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                    >
                      <option value="">Unassigned</option>
                      {filteredAgents.map((a) => (
                        <option key={a.id} value={a.id}>
                          {a.first_name && a.last_name ? `${a.first_name} ${a.last_name}` : a.username}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
                <div className="flex gap-2 pt-1">
                  <button
                    onClick={handleUpdate}
                    className="flex-1 py-2 text-sm font-medium rounded-lg bg-blue-600 hover:bg-blue-700 text-white transition-colors"
                  >
                    Save
                  </button>
                  <button
                    onClick={() => {
                      setEditing(false);
                      setEditForm({
                        status: ticket.status,
                        priority: ticket.priority,
                        agent: ticket.agent || '',
                      });
                    }}
                    className="flex-1 py-2 text-sm font-medium rounded-lg border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-500 dark:text-slate-400">Status</span>
                  <StatusBadge status={ticket.status} />
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-500 dark:text-slate-400">Priority</span>
                  <PriorityBadge priority={ticket.priority} />
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-500 dark:text-slate-400">Team</span>
                  <span className="text-sm text-slate-700 dark:text-slate-300">
                    {ticket.team_name || '--'}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-500 dark:text-slate-400">Department</span>
                  <span className="text-sm text-slate-700 dark:text-slate-300">
                    {ticket.department_name || '--'}
                  </span>
                </div>
                <hr className="border-slate-100 dark:border-slate-800" />
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-500 dark:text-slate-400">Requester</span>
                  <span className="text-sm text-slate-700 dark:text-slate-300">
                    {ticket.requester_name || `#${ticket.requester}`}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-500 dark:text-slate-400">Agent</span>
                  <span className="text-sm text-slate-700 dark:text-slate-300">
                    {ticket.agent_name || 'Unassigned'}
                  </span>
                </div>
                <hr className="border-slate-100 dark:border-slate-800" />
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-500 dark:text-slate-400">Created</span>
                  <span className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {new Date(ticket.created_at).toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-500 dark:text-slate-400">Updated</span>
                  <span className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {new Date(ticket.updated_at).toLocaleString()}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* SLA Status */}
          {ticket.sla_instances && ticket.sla_instances.length > 0 && (
            <div className="bg-white dark:bg-[#0f1729] rounded-xl border border-slate-200 dark:border-slate-800 p-6 space-y-4">
              <div>
                <h2 className="text-sm font-semibold text-slate-900 dark:text-white">SLA Status</h2>
                {ticket.sla_instances[0]?.policy_name && (
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    Policy: {ticket.sla_instances[0].policy_name}
                    {ticket.sla_instances[0]?.schedule_name && (
                      <span className="ml-2 text-slate-400">({ticket.sla_instances[0].schedule_name})</span>
                    )}
                  </p>
                )}
              </div>
              <div className="space-y-3">
                {ticket.sla_instances.map((sla) => {
                  const stateConfig = {
                    active: { color: 'text-blue-600 dark:text-blue-400', bg: 'bg-blue-50 dark:bg-blue-500/10', bar: 'bg-blue-500' },
                    paused: { color: 'text-amber-600 dark:text-amber-400', bg: 'bg-amber-50 dark:bg-amber-500/10', bar: 'bg-amber-500' },
                    fulfilled: { color: 'text-emerald-600 dark:text-emerald-400', bg: 'bg-emerald-50 dark:bg-emerald-500/10', bar: 'bg-emerald-500' },
                    breached: { color: 'text-red-600 dark:text-red-400', bg: 'bg-red-50 dark:bg-red-500/10', bar: 'bg-red-500' },
                  };
                  const metricLabels = {
                    first_reply_time: 'First Reply',
                    next_reply_time: 'Next Reply',
                    pausable_update_time: 'Update Time',
                    requester_wait_time: 'Wait Time',
                    agent_work_time: 'Work Time',
                    total_resolution_time: 'Resolution',
                  };
                  const cfg = stateConfig[sla.state] || stateConfig.active;

                  // Calculate progress
                  let progressPct = 0;
                  let timeLabel = '';
                  if (sla.state === 'fulfilled') {
                    progressPct = 100;
                    timeLabel = 'Completed';
                  } else if (sla.state === 'breached') {
                    progressPct = 100;
                    timeLabel = 'Breached';
                  } else if (sla.due_at && sla.started_at) {
                    const now = Date.now();
                    const start = new Date(sla.started_at).getTime();
                    const due = new Date(sla.due_at).getTime();
                    const total = due - start;
                    const elapsed = now - start;
                    progressPct = total > 0 ? Math.min(Math.round((elapsed / total) * 100), 100) : 0;

                    const remaining = due - now;
                    if (remaining > 0) {
                      const mins = Math.floor(remaining / 60000);
                      const hrs = Math.floor(mins / 60);
                      timeLabel = hrs > 0 ? `${hrs}h ${mins % 60}m left` : `${mins}m left`;
                    } else {
                      timeLabel = 'Overdue';
                    }
                  }

                  const isRequester = role === 'requester';

                  return (
                    <div key={sla.id} className="space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-medium text-slate-600 dark:text-slate-300">
                          {metricLabels[sla.metric] || sla.metric_display || sla.metric}
                        </span>
                        <div className="flex items-center gap-2">
                          {timeLabel && !isRequester && (
                            <span className="text-[10px] text-slate-400 dark:text-slate-500">{timeLabel}</span>
                          )}
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium capitalize ${cfg.bg} ${cfg.color}`}>
                            {sla.state}
                          </span>
                        </div>
                      </div>
                      {!isRequester && (
                        <>
                          <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-1.5">
                            <div
                              className={`${cfg.bar} h-1.5 rounded-full transition-all duration-500`}
                              style={{ width: `${progressPct}%` }}
                            />
                          </div>
                          <div className="flex justify-between text-[10px] text-slate-400 dark:text-slate-500">
                            <span>Target: {sla.target_minutes}m</span>
                            {sla.active_business_minutes != null && (
                              <span>Used: {Math.round(sla.active_business_minutes)}m</span>
                            )}
                          </div>
                        </>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* SLA Audit Timeline (staff only) */}
              {role !== 'requester' && <SLAAuditTimeline ticketId={id} />}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function SLAAuditTimeline({ ticketId }) {
  const [logs, setLogs] = useState([]);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    if (!ticketId) return;
    api.get(`/servicedesk/tickets/${ticketId}/audit-log/`)
      .then((r) => setLogs(Array.isArray(r.data) ? r.data : r.data.results || []))
      .catch(() => {});
  }, [ticketId]);

  if (logs.length === 0) return null;

  const displayLogs = expanded ? logs : logs.slice(0, 3);

  const eventIcons = {
    created: 'bg-blue-100 dark:bg-blue-500/20 text-blue-600 dark:text-blue-400',
    started: 'bg-emerald-100 dark:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400',
    paused: 'bg-amber-100 dark:bg-amber-500/20 text-amber-600 dark:text-amber-400',
    resumed: 'bg-sky-100 dark:bg-sky-500/20 text-sky-600 dark:text-sky-400',
    fulfilled: 'bg-green-100 dark:bg-green-500/20 text-green-600 dark:text-green-400',
    breached: 'bg-red-100 dark:bg-red-500/20 text-red-600 dark:text-red-400',
    cancelled: 'bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-400',
  };

  return (
    <div className="border-t border-slate-100 dark:border-slate-800 pt-4">
      <h3 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-3">
        SLA Timeline
      </h3>
      <div className="space-y-2">
        {displayLogs.map((log) => (
          <div key={log.id} className="flex items-start gap-2.5">
            <div className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${eventIcons[log.event_type] || eventIcons.created}`}>
              <div className="w-1.5 h-1.5 rounded-full bg-current" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs text-slate-700 dark:text-slate-300">
                <span className="font-medium capitalize">{(log.event_type || '').replace(/_/g, ' ')}</span>
                {log.metric && <span className="text-slate-400 ml-1">({(log.metric || '').replace(/_/g, ' ')})</span>}
              </p>
              {log.note && <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-0.5">{log.note}</p>}
              <p className="text-[10px] text-slate-400 dark:text-slate-500">
                {new Date(log.created_at).toLocaleString()}
              </p>
            </div>
          </div>
        ))}
      </div>
      {logs.length > 3 && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-xs text-blue-600 dark:text-blue-400 hover:underline mt-2"
        >
          {expanded ? 'Show less' : `Show all ${logs.length} events`}
        </button>
      )}
    </div>
  );
}
