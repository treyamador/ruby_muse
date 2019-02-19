class PostingsController < ApplicationController
  before_action :authenticate_user!

  def index
    redirect_to root_path
  end

  def create
    @posting = current_user.postings.build(posting_params)
    if @posting.save
      flash[:success] = 'Post created!'
      redirect_to root_path
    else
      render 'new'
    end
  end

  def new
    @posting = Posting.new
  end

  def show
    @postings = current_user.postings.order(created_at: :desc)
  end

  def edit
    @posting = Posting.find(params[:id])
  end

  def update
    @posting = Posting.find(params[:id])
    if @posting.update_attributes(posting_params)
      redirect_to postings_path
    else
      render 'edit'
    end
  end

  def destroy
    posting = Posting.find(params[:id]).destroy
    if posting
      flash[:success] = "Post '#{posting.subject}' destroyed."
      redirect_to root_path
    else
      flash[:danger] = 'An error occured.'
      render 'show'
    end
  end

  def posting_params
    params.require(:posting)
          .permit(:subject, :content, :picture)
  end
end
