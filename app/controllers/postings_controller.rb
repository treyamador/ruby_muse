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
      # TODO add error message
      render 'postings#new'
    end
  end

  def new
    @posting = Posting.new
  end

  def posting_params
    params.require(:posting).permit(:subject, :content)
  end

  def show
    # @postings = current_user.postings
  end

end
